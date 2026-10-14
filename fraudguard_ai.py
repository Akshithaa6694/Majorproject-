import streamlit as st
from google import genai


def show_fraudguard_ai():
    st.markdown("""
    <style>
    .fg-title {
        background: linear-gradient(120deg, #062654, #087fe8);
        color: white;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="fg-title"><h2>🤖 FraudGuard AI</h2>'
        '<p>Ask questions about fraud, transactions, and security.</p></div>',
        unsafe_allow_html=True
    )

    if "fg_messages" not in st.session_state:
        st.session_state.fg_messages = [
            {
                "role": "assistant",
                "content": "Hi! I am FraudGuard AI. Ask me about suspicious transactions, risk scores, or financial security."
            }
        ]

    for message in st.session_state.fg_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask FraudGuard AI a question...")

    if prompt:
        st.session_state.fg_messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            client = genai.Client(api_key=api_key)

            history = "\n".join(
                f'{m["role"]}: {m["content"]}'
                for m in st.session_state.fg_messages[-10:]
            )

            with st.chat_message("assistant"):
                with st.spinner("FraudGuard AI is thinking..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=(
                            "You are FraudGuard AI, a helpful assistant in a "
                            "college financial fraud detection project. Explain "
                            "answers simply. Help users understand suspicious "
                            "transactions, risk scores, fraud prevention, "
                            "machine learning, federated learning, GNNs, and "
                            "explainable AI. Never ask for passwords, PINs, "
                            "OTPs, or CVVs. Do not claim a transaction is "
                            "definitely fraudulent without verified evidence.\n\n"
                            + history
                        )
                    )
                    answer = response.text or (
                        "I couldn't generate a response. Please try again."
                    )
                    st.markdown(answer)

            st.session_state.fg_messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as exc:
            st.error(
                "Gemini could not respond. Check your API key, internet "
                "connection, and API access. Details: " + str(exc)
            )

    if st.button("Clear chat", key="fg_clear_chat"):
        st.session_state.fg_messages = []
        st.rerun()
