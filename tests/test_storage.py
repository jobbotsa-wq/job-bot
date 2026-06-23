import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.storage.db import init_db, already_applied, save_application, get_applications


def test_db_init_and_apply():
    conn = init_db("_test")
    conn.execute("DELETE FROM applications")
    conn.commit()

    job = {
        "id": "linkedin_test_001",
        "title": "Python Developer",
        "company": "Acme Corp",
        "platform": "linkedin",
        "url": "https://linkedin.com/jobs/1",
        "match_score": 85,
        "notes": "test",
    }

    assert not already_applied(conn, job["id"]), "No debería estar aplicado aún"
    save_application(conn, job, status="applied")
    assert already_applied(conn, job["id"]), "Debería estar aplicado ahora"

    apps = get_applications(conn, limit=10)
    assert len(apps) == 1
    assert apps[0]["title"] == "Python Developer"
    assert apps[0]["match_score"] == 85

    # Limpiar
    conn.execute("DELETE FROM applications WHERE job_id = 'linkedin_test_001'")
    conn.commit()
    conn.close()
    print("✓ test_db_init_and_apply OK")


def test_duplicate_apply():
    conn = init_db("_test")
    conn.execute("DELETE FROM applications")
    conn.commit()

    job = {"id": "linkedin_dup_001", "title": "QA", "company": "X",
           "platform": "linkedin", "url": "", "match_score": 70, "notes": ""}

    save_application(conn, job, status="applied")
    save_application(conn, job, status="applied")  # duplicado — no debe fallar

    apps = get_applications(conn)
    assert len(apps) == 1, "No debe haber duplicados"

    conn.execute("DELETE FROM applications")
    conn.commit()
    conn.close()
    print("✓ test_duplicate_apply OK")


if __name__ == "__main__":
    test_db_init_and_apply()
    test_duplicate_apply()
    print("\nTodos los tests pasaron.")
