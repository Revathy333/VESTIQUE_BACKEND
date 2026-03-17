"""
Pulls live data from PostgreSQL and upserts it into ChromaDB as embeddings.
Called on startup and periodically so the vector store stays fresh.
"""
from sqlalchemy import text
from app.database import SessionLocal
from app.vector_store import add_knowledge
from app.vector_store import add_to_collection


def index_designers_and_tailors():
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                u.id,
                u.first_name || ' ' || u.last_name      AS full_name,
                u.role,
                u.business_name,
                ROUND(AVG(pr.rating)::numeric, 1)        AS avg_rating,
                COUNT(DISTINCT pr.id)                    AS review_count,
                COUNT(DISTINCT p.id)                     AS post_count,
                -- pull in general review mentions + ratings
                ROUND(AVG(gr.rating)::numeric, 1)        AS gen_avg_rating,
                COUNT(DISTINCT grm.id)                   AS gen_mention_count
            FROM users u
            LEFT JOIN profile_reviews pr   ON pr.reviewed_user_id = u.id
            LEFT JOIN posts p              ON p.author_id = u.id
            LEFT JOIN general_review_mentions grm ON grm.mentioned_user_id = u.id
            LEFT JOIN general_reviews gr   ON gr.id = grm.review_id
            WHERE u.role IN ('designer', 'tailor')
              AND u.is_active = true
            GROUP BY u.id, u.first_name, u.last_name, u.role, u.business_name
        """)).mappings().all()

        for r in rows:
            doc_id = f"creator_{r['id']}"
            biz = f", works at {r['business_name']}" if r['business_name'] else ""

            # Profile review rating
            if r['avg_rating']:
                profile_rating_str = (
                    f"a profile rating of {r['avg_rating']} stars "
                    f"from {r['review_count']} direct customer reviews"
                )
            else:
                profile_rating_str = "no direct profile reviews yet"

            # General review mention rating
            if r['gen_avg_rating']:
                gen_rating_str = (
                    f"mentioned in {r['gen_mention_count']} community reviews "
                    f"with an average rating of {r['gen_avg_rating']} stars"
                )
            else:
                gen_rating_str = "not mentioned in community reviews yet"

            popularity = (
                "very active" if r['post_count'] >= 5
                else "active" if r['post_count'] >= 2
                else "new"
            )

            text_doc = (
                f"{r['full_name']} is a {r['role']} on Vestique{biz}. "
                f"They have {profile_rating_str}. "
                f"They are {gen_rating_str}. "
                f"They are a {popularity} creator with {r['post_count']} posts. "
                f"Based on available data, this {r['role']} is "
                f"{'highly recommended' if (r['gen_avg_rating'] or 0) >= 4 else 'recommended'} "
                f"on the platform."
            )
            add_to_collection("creators", doc_id, text_doc)

        print(f"✅ Indexed {len(rows)} designers/tailors")
    except Exception as e:
        print(f"⚠️ index_designers_and_tailors error: {e}")
    finally:
        db.close()


def index_profile_reviews():
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                pr.id,
                ru.first_name || ' ' || ru.last_name  AS reviewer_name,
                rd.first_name || ' ' || rd.last_name  AS designer_name,
                rd.role,
                pr.rating,
                pr.text
            FROM profile_reviews pr
            JOIN users ru ON ru.id = pr.reviewer_id
            JOIN users rd ON rd.id = pr.reviewed_user_id
            ORDER BY pr.created_at DESC
            LIMIT 100
        """)).mappings().all()

        for r in rows:
            doc_id = f"profile_review_{r['id']}"
            text_doc = (
                f"Customer {r['reviewer_name']} reviewed {r['designer_name']} "
                f"({r['role']}) and gave {r['rating']} out of 5 stars. "
                f"They said: {r['text']}"
            )
            # add_knowledge(doc_id, text_doc)
            add_to_collection("profile_reviews", doc_id, text_doc)

        print(f"✅ Indexed {len(rows)} profile reviews")
    except Exception as e:
        print(f"⚠️ index_profile_reviews error: {e}")
    finally:
        db.close()


def index_general_reviews():
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                gr.id,
                u.first_name || ' ' || u.last_name   AS reviewer_name,
                gr.text,
                gr.rating,
                STRING_AGG(
                    mu.first_name || ' ' || mu.last_name, ', '
                ) AS mentioned_names
            FROM general_reviews gr
            JOIN users u ON u.id = gr.author_id
            LEFT JOIN general_review_mentions grm ON grm.review_id = gr.id
            LEFT JOIN users mu ON mu.id = grm.mentioned_user_id
            GROUP BY gr.id, u.first_name, u.last_name, gr.text, gr.rating
            ORDER BY gr.created_at DESC
            LIMIT 100
        """)).mappings().all()

        for r in rows:
            doc_id = f"general_review_{r['id']}"
            mentions = f" They mentioned: {r['mentioned_names']}." \
                       if r['mentioned_names'] else ""
            text_doc = (
                f"{r['reviewer_name']} left a {r['rating']}-star review on Vestique. "
                f"They said: {r['text']}{mentions}"
            )
            # add_knowledge(doc_id, text_doc)
            add_to_collection("general_reviews", doc_id, text_doc)

        print(f"✅ Indexed {len(rows)} general reviews")
    except Exception as e:
        print(f"⚠️ index_general_reviews error: {e}")
    finally:
        db.close()


def index_posts():
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                p.id,
                u.first_name || ' ' || u.last_name  AS author_name,
                u.role,
                p.caption,
                p.description,
                COUNT(pl.id)                        AS likes_count
            FROM posts p
            JOIN users u ON u.id = p.author_id
            LEFT JOIN post_likes pl ON pl.post_id = p.id
            WHERE u.role IN ('designer', 'tailor')
            GROUP BY p.id, u.first_name, u.last_name, u.role,
                     p.caption, p.description
            ORDER BY p.created_at DESC
            LIMIT 100
        """)).mappings().all()

        for r in rows:
            doc_id = f"post_{r['id']}"
            desc = r['description'] or r['caption'] or ""
            if not desc.strip():
                continue
            text_doc = (
                f"{r['author_name']} ({r['role']}) posted on Vestique: "
                f"\"{desc[:300]}\". "
                f"This post has {r['likes_count']} likes."
            )
            # add_knowledge(doc_id, text_doc)
            add_to_collection("posts", doc_id, text_doc)

        print(f"✅ Indexed {len(rows)} posts")
    except Exception as e:
        print(f"⚠️ index_posts error: {e}")
    finally:
        db.close()


def index_all():
    """Index everything — call on startup and periodically."""
    print("🔄 Starting full DB indexing into ChromaDB...")
    index_designers_and_tailors()
    index_profile_reviews()
    index_general_reviews()
    index_posts()
    print("✅ Full DB indexing complete.")