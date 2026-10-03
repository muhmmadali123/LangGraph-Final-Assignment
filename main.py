from app.graph.workflow import workflow


def main():
    print("=" * 60)
    print("LangGraph Final Assignment")
    print("Multi-Agent AI System")
    print("=" * 60)
    print("Type 'exit' or 'quit' to stop.")
    print("Press Ctrl+C anytime to stop.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit"}:
                print("\nGoodbye! 👋")
                break

            result = workflow.invoke(
                {
                    "user_input": user_input,
                    "response": "",
                }
            )

            print(f"\nAI: {result['response']}")

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break

        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    main()