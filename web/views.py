import json
import os
import random

from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.utils.html import escape, strip_tags


def index(request):
    with open("web/thesauruses/meta_info.json", 'r') as meta_file:
        meta_data = meta_file.read()
    meta_data_langs = json.loads(meta_data)["languages"]
    meta_structures = json.loads(meta_data)["structures"]
    random_langs = random.sample(list(meta_data_langs.values()), k=3)

    content = {
        'title': 'Welcome',
        'languages': meta_data_langs,
        'structures': meta_structures,
        'randomLanguages': random_langs,
    }
    return render(request, 'index.html', content)


def about(request):
    content = {
        'title': 'About'
    }
    return render(request, 'about.html', content)


class Language(object):
    def __init__(self, key):
        self.key = key

    def has_key(self):
        return self.key == ""

    def load_structure(self, structure_key):
        file_path = os.path.join(
            "web", "thesauruses", self.key, structure_key) + ".json"
        with open(file_path, 'r') as file:
            data = file.read()
            # parse file
            file_json = json.loads(data)

            self.friendly_name = file_json["meta"]["language_name"]
            self.categories = file_json["categories"]
            self.concepts = file_json[structure_key]

    def concept(self, concept_key):
        if self.concepts.get(concept_key) is None:
            return {
                "code": "",
                "comment": ""
            }
        else:
            return self.concepts.get(concept_key)

    def concept_code(self, concept_key):
        return self.concept(concept_key)["code"]

    def concept_comment(self, concept_key):
        return self.concept(concept_key).get("comment", "")


class MetaInfo(object):
    def __init__(self):
        with open("web/thesauruses/meta_info.json", 'r') as meta_file:
            meta_data = meta_file.read()
        self.data_structures = json.loads(meta_data)["structures"]

    def structure_friendly_name(self, structure_key):
        index = list(self.data_structures.values()).index(structure_key)
        return list(self.data_structures.keys())[index]

    def structure(self, structure_key):
        return MetaStructure(structure_key, self.structure_friendly_name(structure_key))


class MetaStructure(object):
    def __init__(self, structure_key, friendly_name):
        self.key = structure_key
        self.friendly_name = friendly_name
        meta_structure_file_path = os.path.join(
            "web", "thesauruses", "_meta", structure_key) + ".json"
        with open(meta_structure_file_path, 'r') as meta_structure_file:
            data = meta_structure_file.read()
            # parse file
            meta_structure_file_json = json.loads(data)

            self.categories = meta_structure_file_json["categories"]
            self.concepts = meta_structure_file_json[structure_key]



def compare(request):
    lang1 = Language(escape(strip_tags(request.GET.get('lang1', ''))))
    lang2 = Language(escape(strip_tags(request.GET.get('lang2', ''))))
    structure_query_string = escape(strip_tags(request.GET.get('concept', '')))

    if not lang1.has_key and lang2.has_key:
        return HttpResponseNotFound(
            "The " + structure_query_string + " concept of either the " + lang1.key + " or " +
            lang2.key + " languages doesn't exist or hasn't been implemented yet.")

    metainfo = MetaInfo()
    meta_structure = metainfo.structure(structure_query_string)

    try:
        lang1.load_structure(meta_structure.key)
        lang2.load_structure(meta_structure.key)

    except:
        return HttpResponseNotFound(
            "The " + meta_structure.friendly_name + " concept of either the " + lang1.key + " or " +
            lang2.key + " languages doesn't exist or hasn't been implemented yet.")

    both_categories = []
    both_concepts = []
    # XXX: Ideally we should set default value of lang dict here
    # and not in template but that will be possible after issue #27
    # is resolved

    all_category_keys = list(meta_structure.categories.keys())
    all_concept_keys = list(meta_structure.concepts.keys())

    for category_key in all_category_keys:
        both_categories.append({
            "id": category_key,
            "concepts": meta_structure.categories[category_key]
        })

    # Start Building Response Structure
    for concept_key in all_concept_keys:
        both_concepts.append({
            "id": concept_key,
            "name": meta_structure.concepts[concept_key]["name"],
            "code1": lang1.concept_code(concept_key),
            "code2": lang2.concept_code(concept_key),
            "comment1": lang1.concept_comment(concept_key),
            "comment2": lang2.concept_comment(concept_key)
        })

    # establish order listing across all languages
    # common_concepts.sort(key=lambda x: x["key"])

    # DB equivalent of full outer join
    response = {
        "title": "Comparing" + lang1.friendly_name + " " + lang2.friendly_name,
        "concept": meta_structure.key,
        "concept_friendly_name": meta_structure.friendly_name,
        "lang1": lang1.key,
        "lang2": lang2.key,
        "lang1_friendlyname": lang1.friendly_name,
        "lang2_friendlyname": lang2.friendly_name,
        "categories": both_categories,
        "concepts": both_concepts
    }

    return render(request, 'compare.html', response)


def reference(request):

    lang = Language(escape(strip_tags(request.GET.get('lang', ''))))
    structure_query_string = escape(strip_tags(request.GET.get('concept', '')))
    if not lang.has_key:
        return HttpResponseNotFound(
            "The " + structure_query_string + " concept of the " + lang.key + " language doesn't exist or hasn't been implemented yet.")

    metainfo = MetaInfo()
    meta_structure = metainfo.structure(structure_query_string)

    try:
        lang.load_structure(meta_structure.key)

    except:
        return HttpResponseNotFound(
            "The " + meta_structure.friendly_name + " concept of the " + lang.key + " language doesn't exist or hasn't been implemented yet.")

    categories = []
    concepts = []
    for category_key in lang.categories:
        categories.append({
            "id": category_key,
            "concepts": meta_structure.categories[category_key] # meta_lang_categories[category_key]
        })

    for concept_key in lang.concepts:
        concepts.append({
            "id": concept_key,
            "name": meta_structure.concepts[concept_key]["name"],
            "code": lang.concept_code(concept_key),
            "comment": lang.concept_comment(concept_key)
        })

    response = {
        "title": "Reference for " + lang.key,
        "concept": meta_structure.key,
        "concept_friendly_name": meta_structure.friendly_name,
        "lang": lang.key,
        "lang_friendlyname": lang.friendly_name,
        "categories": categories,
        "concepts": concepts
    }

    return render(request, 'reference.html', response)
