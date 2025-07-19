import nox


@nox.session(python="3.13")
def tests(session: nox.Session) -> None:
    """Run all tests."""
    session.install(".[test]")
    session.run("pytest", *session.posargs)
