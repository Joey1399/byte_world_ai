"""CLI entrypoint for byte_world_ai."""

from game.engine import Engine
from game.state import create_initial_state


def main() -> None:
    """Start the game loop."""
    state = create_initial_state()
    engine = Engine()
    engine.run(state)


if __name__ == "__main__":
    main()
