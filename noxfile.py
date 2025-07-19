import nox


@nox.session(python="3.13")
def tests(session: nox.Session) -> None:
    """Run all tests."""
    session.install(".[test]")
    session.run("pytest", *session.posargs)


# tests:
# Simulator -> make event
# Encoder -> encode it
# Decoder -> decode it, see if it matches before encoder
# Geometry: -> make test geometry, test that the geometry matches
# hthe
# hhhhh