import re
import os
import yaml
import pytholog as pl
from enum import Enum, auto
from dataclasses import dataclass
from dataclasses import asdict


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
        query_arr = query.lower().split()

        pluralize = lambda word : word + 'es' if word.endswith(('s','x','z','ch','sh','ss')) else word + 's'

        processed_arr = []
        for token in query_arr:
             if token in self.synonyms:
                 processed_arr.append(self.synonyms[token])
             elif token.endswith('es') and token[:-2] in self.synonyms:
                 processed_arr.append(pluralize(self.synonyms[token[:-2]]))
             elif token.endswith('s') and token[:-1] in self.synonyms:
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
        if match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name, value, addition_prefix, addition = match.groups()
        #matches "Which Dog eat at night?"
        elif match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name, addition_prefix, addition = match.groups()
        #matches "Which Dog eat apples?"
        elif match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name, value = match.groups()
        #matches "Which Dog eat?"
        elif match := re.search(r'(?:.* |^)(which) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name = match.groups()

        #matches "Who eat at night?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)', query):
            question, rule_name, addition_prefix, addition = match.groups()
        #matches "Who eat apples at night?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)', query):
            question, rule_name, value, addition_prefix, addition = match.groups()
        #matches "Who eat apples?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, rule_name, value = match.groups()
        #matches "Who eat?"
        elif match := re.search(r'(?:.* |^)(who) ([a-zA-Z0-9]+)', query):
            question, rule_name = match.groups()

        #matches "What Dog of user eat at night?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)', query):
            question, subject, belong, rule_name, addition_prefix, addition = match.groups()
        #matches "What Dog eat at night?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name, addition_prefix, addition = match.groups()
        #matches "What dog of user eat?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, belong, rule_name = match.groups()
        #matches "What Dog eat?"
        elif match := re.search(r'(?:.* |^)(what) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name = match.groups()

        #matches "When Dog of user eat apples?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, belong, rule_name, value = match.groups()
        #matches "When Dog eat the apples?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name, value = match.groups()
        #matches "When dog of user eat?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, belong, rule_name = match.groups()
        #matches "When Dog eat?"
        elif match := re.search(r'(?:.* |^)(when|where) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)', query):
            question, subject, rule_name = match.groups()

        #matches "dog of user eat apples at night" or "dog of user eat apples at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)(\?)?', query):
            subject, belong, rule_name, value, addition_prefix, addition, question = match.groups()
        #matches "dog eat apples at night" or "dog eat apples at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)(\?)?', query):
            subject, rule_name, value, addition_prefix, addition, question = match.groups()
        #matches "Dog of user eat at night" or "Dog of user eat at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)(\?)?', query):
            subject, belong, rule_name, addition_prefix, addition, question = match.groups()
        #matches "Dog eat at night" or "Dog eat at night?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) ([a-zA-Z0-9]+) (in|at) ([a-zA-Z0-9]+)(\?)?', query):
            subject, rule_name, addition_prefix, addition, question = match.groups()
        #matches "Dog of user eat apples" or "Dog of user eat apples?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)(\?)?', query):
            subject, belong, rule_name, value, question = match.groups()
        #matches "Dog eat apples" or "Dog eat apples?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)(\?)?', query):
            subject, rule_name, value, question = match.groups()
        #matches "Dog of user eat" or "Dog of user eat?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) of ([a-zA-Z0-9]+) ([a-zA-Z0-9]+)(\?)?', query):
            subject, belong, rule_name, question = match.groups()
        #matches "Dog eat" or "Dog eat?"
        elif match := re.search(r'(?:.* |^)([a-zA-Z0-9]+) ([a-zA-Z0-9]+)(\?)?', query):
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
                    sen.addition_prefix = 'VarP'
                    sen.addition = 'Var'
                case SentenceType.WhereQuestion:
                    sen.addition_prefix = 'VarP'
                    sen.addition = 'Var'
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
            if belong:
                base += f" of {belong}"
            if negative:
                if value:
                    sentence_str = f"No {base} {rule}s {value}".strip()
                else:
                    sentence_str = f"No {base} {rule}s.".strip()
            else:
                sentence_str = f"{base} of {reply_values}".strip()
        elif sentence.stype == SentenceType.WhenQuestion:
            # e.g., "Dog eats uranium at night." or negative: "No dog eats uranium."
            varp = ""
            var = ""
            if reply and isinstance(reply[0], dict):
                varp = reply[0].get("VarP", "")
                var = reply[0].get("Var", "")
            base = f"{subject} {rule} {value}".strip()
            if belong:
                base += f" of {belong}"
            if not negative:
                base += f" {varp} {var}"
            elif add_prefix and negative:
                base = f"No {subject} {rule} {value}".strip()
            sentence_str = base
        elif sentence.stype == SentenceType.WhereQuestion:
            # e.g., "Dog eats urandoium at home." or negative: "No dog eats uranium."
            varp = ""
            var = ""
            if reply and isinstance(reply[0], dict):
                varp = reply[0].get("VarP", "")
                var = reply[0].get("Var", "")
            base = f"{subject} {rule} {value}".strip()
            if belong:
                base += f" of {belong}"
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
        
        # Capitalize the first letter and add a period.
        if sentence_str:
            sentence_str = sentence_str[0].upper() + sentence_str[1:] + "."
        return sentence_str




#testing zone 	▓▒░(°◡°)░▒▓
if __name__ == '__main__': 
    lux = Lux(os.path.dirname(__file__) + '/data.yaml')
    print('LUX INITIALIZED')
    print('----DIALOGUE START----')
    while True:
        query = input()
        reply = lux.think(query)
        print('LUX: - ',reply)
