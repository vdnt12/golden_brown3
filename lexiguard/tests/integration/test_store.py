
import pytest

from app.retrieval.lexical import fts_match_query, search_chunks
from app.store.chunks import ChunkInsert, count_chunks
from app.store.db import init_db, pragma_report
from app.store.documents import create_document, get_document
from app.store.fts import index_chunk, purge_document
from app.store.pages import get_page, insert_page
from app.store.sentences import SentenceInsert, get_sentence, insert_sentences


@pytest.fixture
def db(tmp_path):
    connection = init_db(tmp_path / "doc.sqlite3")
    yield connection
    connection.close()


def seed(connection):
    create_document(
        connection,
        doc_id="a" * 32,
        sha256="c" * 64,
        source_filename="synthetic.txt",
        source_kind="txt",
        page_count=1,
        parser_version="scaffold",
    )
    sentence_text = "The deposit is Rs. 25,000/- per month."
    insert_page(connection, doc_id="a" * 32, page_no=1, text=sentence_text + "\n")
    insert_sentences(
        connection,
        "a" * 32,
        [
            SentenceInsert(
                sid="s_0001",
                page_no=1,
                section="2",
                char_start=0,
                char_end=len(sentence_text),
                text=sentence_text,
            )
        ],
    )
    index_chunk(
        connection,
        "a" * 32,
        ChunkInsert(
            ev_id="ev_0001",
            section="2",
            heading="Deposit",
            char_start=0,
            char_end=len("The deposit is Rs. 25,000/- per month."),
            text="The deposit is Rs. 25,000/- per month.",
            sentence_ids=["s_0001"],
        ),
    )


def test_pragmas_are_secure(db):
    report = pragma_report(db)
    assert int(report["secure_delete"]) == 1
    assert str(report["journal_mode"]).lower() == "delete"
    assert int(report["foreign_keys"]) == 1


def test_document_page_and_sentence_round_trip(db):
    seed(db)
    doc = get_document(db, "a" * 32)
    assert doc["page_count"] == 1
    page = get_page(db, "a" * 32, 1)
    sentence = get_sentence(db, "a" * 32, "s_0001")
    assert page["text"][sentence["char_start"]:sentence["char_end"]] == sentence["text"]


def test_fts_finds_numbers_and_words(db):
    seed(db)
    assert count_chunks(db, "a" * 32) == 1
    by_number = search_chunks(db, "a" * 32, "25000")
    by_word = search_chunks(db, "a" * 32, "deposit")
    assert len(by_number) == 1
    assert len(by_word) == 1
    assert by_number[0]["ev_id"] == "ev_0001"


def test_fts_query_neutralises_operators():
    assert fts_match_query('deposit OR "rent" -x*') == '"deposit" OR "OR" OR "rent" OR "x"'


def test_purge_removes_rows_and_fts_shadows(db):
    seed(db)
    purge_document(db, "a" * 32)
    assert count_chunks(db, "a" * 32) == 0
    assert get_document(db, "a" * 32) is None
    assert search_chunks(db, "a" * 32, "deposit") == []


def test_repeated_clause_headings_do_not_collide(db):
    """Real contracts repeat headings; the clause map must accept that."""
    from app.retrieval.clause_map import ClauseEntry, ClauseMap
    from app.store.clauses import replace_clause_map

    seed(db)
    entries = [
        ClauseEntry(label="Notices", page=1, sid_first="s_0001", sid_last="s_0002", sentence_count=2),
        ClauseEntry(label="Notices", page=4, sid_first="s_0020", sid_last="s_0021", sentence_count=2),
    ]
    replace_clause_map(db, "a" * 32, ClauseMap(entries=entries))
    rows = db.execute("SELECT clause_id, page_no FROM clauses ORDER BY page_no").fetchall()
    assert len(rows) == 2
    assert len({row["clause_id"] for row in rows}) == 2
