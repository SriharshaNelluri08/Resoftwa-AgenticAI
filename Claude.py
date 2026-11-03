import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
       model="claude-haiku-5-5",
       max_tokens=200,
       messages=[
           {"role": "user", "content": "Say hello and give me one fun fact in two sentences."}
       ],
   )
print(message.content[0].text)