import re
import os
import yaml
import pytholog as pl
from enum import Enum, auto
from dataclasses import dataclass
from dataclasses import asdict
import customtkinter as ctk
from tkinter import scrolledtext
import time
import threading
import tkinter as tk

class SentenceType(Enum):
    Statement =  auto()
    Question = auto()
    WhatQuestion = auto()
    WhichQuestion = auto()
    WhenQuestion = auto()
    WhereQuestion = auto()
    WhoQuestion = auto()


class Lux():
    def __init__(self, datafile : str):
        with open(datafile, 'r') as file:
             self.data = yaml.safe_load(file)
        self.lexer = Lexer(self.data['synonyms'], self.data['concats'])
        self.parser = Parser()
        self.processor = Processor(self.data['rules'])
        self.translator = Translator()

    
    def think(self, query):
        preprocessed = self.lexer.preprocess(query)
        sentence = lux.parser.parse(preprocessed)
        # print (sentence)
        reply = lux.processor.process_query(sentence)

        translated = lux.translator.translate(sentence, reply)
        return translated
        

class Lexer():

    def __init__(self, synonyms : dict[str, str], concats : list[str]):
        self.synonyms = synonyms
        self.concats = concats

    def preprocess(self, query : str):
        query = query.replace('?',' ?').replace('!','')
        query_arr = query.lower().split()

        pluralize = lambda word : word + 'es' if word.endswith(('s','x','z','ch','sh','ss')) else word + 's'

        processed_arr = []
        for token in query_arr:
             if token in self.synonyms:
                 processed_arr.append(self.synonyms[token])
             elif token in {"a", "an", "the"}:  # Пропускаємо артиклі
                 continue
             elif token.endswith('es') and token[:-2] in self.synonyms:
                 processed_arr.append(pluralize(self.synonyms[token[:-2]]))
             elif token.endswith('s') and token[:-1] in self.synonyms and token != 'is':
                 processed_arr.append(pluralize(self.synonyms[token[:-1]]))
             else:
                 processed_arr.append(token)
        processed = ' '.join(processed_arr)

        for phrase in self.concats:
            if phrase in processed:
                processed = processed.replace(phrase, phrase.replace(' ','_'))
        
        return processed

class Parser():
    
    def parse(self, query : str):
        sen_type = SentenceType.Statement
        question = subject = belong = rule_name = value = addition_prefix = addition = None

        #matches "Which Dog eat apples at night?"
        if match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name, value, addition_prefix, addition = match.groups()
        #matches "Which Dog eat at night?"
        elif match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name, addition_prefix, addition = match.groups()
        #matches "Which Dog eat apples?"
        elif match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name, value = match.groups()
        #matches "Which Dog eat?"
        elif match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name = match.groups()

        #matches "Who eat at night?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+)', query):
            question, rule_name, addition_prefix, addition = match.groups()
        #matches "Who eat apples at night?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+)', query):
            question, rule_name, value, addition_prefix, addition = match.groups()
        #matches "Who eat apples?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, rule_name, value = match.groups()
        #matches "Who eat?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9_]+)', query):
            question, rule_name = match.groups()

        #matches "What Dog of user eat at night?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+)', query):
            question, subject, belong, rule_name, addition_prefix, addition = match.groups()
        #matches "What dog of user eat?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, belong, rule_name = match.groups()
        #matches "What Dog eat at night?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name, addition_prefix, addition = match.groups()
        #matches "What Dog eat?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name = match.groups()

        #matches "When Dog of user eat apples?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, belong, rule_name, value = match.groups()
        #matches "When dog of user eat?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, belong, rule_name = match.groups()
        #matches "When Dog eat the apples?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name, value = match.groups()
        #matches "When Dog eat?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)', query):
            question, subject, rule_name = match.groups()

        #matches "dog of user eat apples at night" or "dog of user eat apples at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, belong, rule_name, value, addition_prefix, addition, question = match.groups()
        #matches "Dog of user eat at night" or "Dog of user eat at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, belong, rule_name, addition_prefix, addition, question = match.groups()
        #matches "dog eat apples at night" or "dog eat apples at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, rule_name, value, addition_prefix, addition, question = match.groups()
        #matches "Dog eat at night" or "Dog eat at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) (in|at) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, rule_name, addition_prefix, addition, question = match.groups()
        #matches "Dog of user eat apples" or "Dog of user eat apples?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, belong, rule_name, value, question = match.groups()
        #matches "Dog of user eat" or "Dog of user eat?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) of ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, belong, rule_name, question = match.groups()
        #matches "Dog eat apples" or "Dog eat apples?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, rule_name, value, question = match.groups()
        #matches "Dog eat" or "Dog eat?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+) ?(\?)?', query):
            subject, rule_name, question = match.groups()
        
        rule_name = 'has' if rule_name == 'is' else rule_name

        match question:
            case 'when':
                question = SentenceType.WhenQuestion
            case 'where':
                question = SentenceType.WhereQuestion
            case 'what':
                question = SentenceType.WhatQuestion
            case 'who':
                question = SentenceType.WhoQuestion
            case 'which':
                question = SentenceType.WhichQuestion
            case '?':
                question = SentenceType.Question

        sen_type = question if question != None and type(question) is SentenceType else sen_type
        
        return Sentence(sen_type, subject, belong, rule_name, value, addition_prefix, addition)

@dataclass
class Sentence():

    stype : SentenceType
    subject : str
    belong : str
    rule_name : str
    value : str
    addition_prefix : str
    addition : str

class Processor():

    def __init__(self, rules : list[str]):
        self.rules = rules
        self.engine = pl.KnowledgeBase("world")
        self.engine(rules)
    
    def _add_rule(self, rule : str):
        self.engine.add_kn([rule])
        self.engine._cache = {}

    def _question(self, question: str):
        try:
            result = self.engine.query(pl.Expr(question))
            self.engine._cache = {}
        except TypeError:
            # If pytholog fails (e.g., due to an unexpected None), return an empty list.
            return []
        return result if result is not None else []

    
    def _convert_none_to_any_variable(self, sen : Sentence):
        field_dict = asdict(sen)
        converted = { key:'_' if value == None else value for (key,value) in field_dict.items()}
        return Sentence(**converted)
    
    def process_query(self, sen : Sentence):
        #add more variativity by adding to data.yaml several predefined responses for certain situations
        reply = 'Thank you for information!'
        if sen.stype == SentenceType.Statement:
            rule = f'{sen.rule_name}({sen.subject}, {sen.belong}, {sen.value}, {sen.addition_prefix}, {sen.addition})'
            self._add_rule(rule)
        elif sen.stype == SentenceType.Question:
            sen = self._convert_none_to_any_variable(sen) 
            question = f'{sen.rule_name}({sen.subject}, {sen.belong}, {sen.value}, {sen.addition_prefix}, {sen.addition})'
            reply = self._question(question)
        else:
            match sen.stype:
                case SentenceType.WhatQuestion:
                    sen.value = 'Var'
                case SentenceType.WhichQuestion:
                    sen.belong = 'Var'
                case SentenceType.WhenQuestion:
                    #sen.addition_prefix = 'VarP'
                    sen.addition = 'Var'
                    sen.addition_prefix = 'at'
                case SentenceType.WhereQuestion:
                    #sen.addition_prefix = 'VarP'
                    sen.addition = 'Var'
                    sen.addition_prefix = 'in'
                case SentenceType.WhoQuestion:
                    sen.subject = 'Var'
            sen = self._convert_none_to_any_variable(sen) 
            question = f'{sen.rule_name}({sen.subject}, {sen.belong}, {sen.value}, {sen.addition_prefix}, {sen.addition})' 
            reply = self._question(question)
        
        return reply


class Translator():
  

    def safe(self, val):
        return val if val is not None else ""
        

    def translate(self, sentence, reply):

        subject = self.safe(sentence.subject)
        belong = self.safe(sentence.belong)
        rule = self.safe(sentence.rule_name)
        value = self.safe(sentence.value)
        add_prefix = self.safe(sentence.addition_prefix)

        if subject == 'user':
            subject = 'you'
        if belong == 'user':
            belong = 'yours'
        if value == 'user':
            value = 'you'
        
        if sentence.stype == SentenceType.Statement:
            return reply
        
        if not reply:
            return "I could not find an answer."
        
        extracted_replies = []
        for item in reply:
            if isinstance(item, dict):
                extracted_replies.append(item.get("Var", ""))
            elif isinstance(item, str):
                extracted_replies.append(item)
            else:
                extracted_replies.append(str(item))
        reply_values = ", ".join(ans for ans in extracted_replies if ans)

        negative = reply_values.lower() in {"no", "none", ""}
        
        sentence_str = ""
        if sentence.stype == SentenceType.WhatQuestion:
            # e.g., "Dog of Sasha eats uranium." or negative: "No dog eats uranium."
            base = f"{subject}"
            if belong:
                base += f" of {belong}"
            if negative:
                sentence_str = f"I don't know"
            else:
                sentence_str = f"{base} {rule} {reply_values}".strip()
        elif sentence.stype == SentenceType.WhichQuestion:
            # e.g., "Dog of sasha, misha." or negative: "No dog eats uranium."
            base = subject
            if negative:
                if value:
                    sentence_str = f"No {base} {rule}s {value}".strip()
                else:
                    sentence_str = f"No {base} {rule}s.".strip()
            else:
                sentence_str = f"{base} of {reply_values}".strip()
        elif sentence.stype == SentenceType.WhenQuestion:
            # e.g., "Dog eats uranium at night." or negative: "No dog eats uranium."
            varp = "at"
            var = ""
            if reply and isinstance(reply[0], dict):
                var = reply[0].get("Var", "")
            if belong:
                subject = f"{subject} of {belong}"
            base = f"{subject} {rule} {value}".strip()
            if not negative:
                base += f" {varp} {var}"
            elif add_prefix and negative:
                base = f"No {subject} {rule} {value}".strip()
            sentence_str = base
        elif sentence.stype == SentenceType.WhereQuestion:
            # e.g., "Dog eats urandoium at home." or negative: "No dog eats uranium."
            varp = "in"
            var = ""
            if reply and isinstance(reply[0], dict):
                var = reply[0].get("Var", "")
            if belong:
                subject = f"{subject} of {belong}"
            base = f"{subject} {rule} {value}".strip()
            if not negative:
                base += f" {varp} {var}"
            elif add_prefix and negative:
                base = f"No {subject} {rule} {value}".strip()
            sentence_str = base
        elif sentence.stype == SentenceType.WhoQuestion:
            # e.g., "Dog eats uranium." or negative: "No dog eat uranium."
            if negative:
                if value:
                    sentence_str = f"No {subject} {rule} {value}".strip()
                else:
                    sentence_str = f"No {subject} {rule}.".strip()
            else:
                sentence_str = f"{reply_values} {rule} {value}".strip()
        else:
            sentence_str = " ".join([reply_values]).strip()
        
        # Capitalize the first letter and add a period
        if sentence_str:
            sentence_str = sentence_str[0].upper() + sentence_str[1:] + "."
        
        #replace underscores from compound idioms
        if sentence_str:
            sentence_str = sentence_str.replace('_',' ')

        return sentence_str


#testing zone 	▓▒░(°◡°)░▒▓
if __name__ == '__main__':
    lux = Lux(os.path.dirname(__file__) + '/data.yaml')
    print('LUX INITIALIZED')

    # Initialize the main window with a dark theme
    ctk.set_appearance_mode("Dark")  # Dark mode
    ctk.set_default_color_theme("dark-blue")

    app = ctk.CTk()
    app.title("LUX Chatbot")
    app.geometry("500x600")
    app.resizable(False, False)

    # Configure grid layout
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)

    # Conversation Frame
    conversation_frame = ctk.CTkFrame(app, fg_color="#1e1e1e")
    conversation_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # Custom Scrollbar
    scrollbar = ctk.CTkScrollbar(conversation_frame, fg_color="#2a2a2a")
    scrollbar.pack(side="right", fill="y")

    # Scrolled Text Widget for Chat
    conversation = tk.Text(
        conversation_frame,
        wrap="word",
        state='disabled',
        font=("Arial", 20),
        bg="#1e1e1e",
        fg="white",
        bd=0,
        highlightthickness=0,
        padx=10,
        pady=10,
        yscrollcommand=scrollbar.set
    )
    conversation.pack(padx=10, pady=10, fill="both", expand=True)
    scrollbar.configure(command=conversation.yview)

    # Input Field & Button Frame
    input_frame = ctk.CTkFrame(app, fg_color="#1e1e1e")  
    input_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

    user_input = ctk.CTkEntry(
        input_frame,
        placeholder_text="Type a message...",
        font=("Consolas", 13),
        fg_color="#2a2a2a",
        text_color="white",
        border_width=0,
        corner_radius=25,
        height=45
    )
    user_input.pack(side="left", padx=10, pady=10, fill="x", expand=True)

    # Modern Send Button
    send_button = ctk.CTkButton(
        input_frame,
        text="Send",
        font=("Consolas", 16),
        fg_color="#C983DD",
        hover_color="#A66DB6",
        text_color="white",
        corner_radius=25,
        width=50,
        height=45
    )
    send_button.pack(side="right", padx=10, pady=10)

    # Function to Print Bot's Message Letter by Letter
    def type_response(reply):
        conversation.config(state='normal')
        conversation.insert("end", "\n\n", "spacing")
        conversation.insert("end", "LUX:\n", "bot_label")
        conversation.config(state='disabled')

        def type_effect():
            conversation.config(state='normal')
            for letter in reply:
                conversation.insert("end", letter, "bot_message")
                conversation.yview("end")
                time.sleep(0.03)  # Adjust typing speed here
                conversation.update()
            conversation.insert("end", "\n", "bot_message")
            conversation.config(state='disabled')

        threading.Thread(target=type_effect, daemon=True).start()

    # Function to Send Messages
    def send_message():
        query = user_input.get().strip()
        if not query:
            return

        conversation.config(state='normal')
        conversation.insert("end", "\n\n", "spacing")
        conversation.insert("end", "You:\n", "user_label")
        conversation.insert("end", f"{query}\n", "user_message")
        conversation.config(state='disabled')
        user_input.delete(0, "end")
        conversation.yview("end")

        # Chatbot Response
        reply = lux.think(query)
        type_response(reply)

    # Bind "Enter" Key & Button Click to Send Message
    app.bind('<Return>', lambda event: send_message())
    send_button.configure(command=send_message)

    # Styling Chat Bubbles
    conversation.tag_configure("user_label", foreground="#A0A0A0", font=("Arial", 11, "italic"), justify="right")
    conversation.tag_configure("bot_label", foreground="#A0A0A0", font=("Arial", 11, "italic"))

    conversation.tag_configure(
        "user_message",
        foreground="white",
        lmargin1=100,
        lmargin2=100,
        rmargin=10,
        spacing3=10,
        wrap="word",
        justify="right",
        font=("Consolas", 19),
        borderwidth=0,
        relief="flat"
    )

    conversation.tag_configure(
        "bot_message",
        foreground="white",
        lmargin1=10,
        lmargin2=10,
        rmargin=100,
        spacing3=10,
        wrap="word",
        justify="left",
        font=("Consolas", 19),
        borderwidth=0,
        relief="flat"
    )

    conversation.tag_configure("spacing", spacing1=5, spacing3=5)

    # Start the Main Loop
    app.mainloop()
