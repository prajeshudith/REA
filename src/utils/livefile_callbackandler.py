from langchain.callbacks.base import BaseCallbackHandler

class LiveFileCallbackHandler(BaseCallbackHandler):
    def __init__(self, filename):
        self.file = open(filename, 'a')
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.file.write(f"LLM started with prompts: {prompts}\n")
        self.file.flush()  # Force write to disk
    
    def on_llm_end(self, response, **kwargs):
        self.file.write(f"LLM response: {response}\n")
        self.file.flush()
    
    def on_agent_action(self, action, **kwargs):
        self.file.write(f"Agent action: {action.log}\n")
        self.file.flush()
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        self.file.write(f"Tool started: {serialized.get('name')} with input: {input_str}\n")
        self.file.flush()
    
    def on_tool_end(self, output, **kwargs):
        self.file.write(f"Tool output: {output}\n")
        self.file.flush()
    
    def on_text(self, text, **kwargs):
        self.file.write(f"Text: {text}\n")
        self.file.flush()
    
    def __del__(self):
        self.file.close()
