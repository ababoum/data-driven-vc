from openai import AsyncOpenAI


async def get_gpt_summary(text: str, apikey: str) -> str:
    """Get summary from ChatGPT."""
    try:
        prompt = f"Explain this to me in details in markdown format by always keeping your answer objective and concise and by assuming I'm a VC who doesn't know anything about tech (Always try to comment on how it could be a pro or a con in the context of a future investment): {text}"
        client = AsyncOpenAI(api_key=apikey)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling ChatGPT API: {str(e)}")
        return f"Failed to generate summary: {str(e)}"
