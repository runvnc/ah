import inspect
import traceback
import json
import logging
from typing import List, Dict, Optional
from .preferences import find_preferred_models
from .organize_models import uses_models, matching_models
from .check_args import *
import sys
from termcolor import colored


class ProviderManager:
    def __init__(self):
        self.functions = {}

    def register_function(self, name, provider, implementation, signature, docstring, flags):
        if name not in self.functions:
            self.functions[name] = []

        if provider in [func_info['provider'] for func_info in self.functions[name]]:
            print(f"provider {provider} already registered for function {name}")
            return

        self.functions[name].append({
            'implementation': implementation,
            'docstring': docstring,
            'flags': flags,
            'provider': provider
        })
        print("registered function: ", name, provider, implementation, signature, docstring, flags)

    
    async def execute(self, name, *args, **kwargs):
        print(f"execute: {name} called")

        if check_empty_args(args, kwargs=kwargs):
            raise ValueError(f"function '{name}' called with empty arguments.")

        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        preferred_models = None
        preferred_provider = None

        found_context = False
        context = None
        for arg in args:
            if arg.__class__.__name__ == 'ChatContext':
                found_context = True
                context = arg
                break
        

        if not found_context and not ('context' in kwargs):
            kwargs['context'] = self.context
            context = self.context

        print("context is ", context)
        need_model = uses_models(name)

        if context.__class__.__name__ == 'ChatContext':
            preferred_models = await find_preferred_models(name, context.flags)
            context.data['model'] = None

            if need_model and preferred_models is None:
                print("Did not find preferred, loading all matching based on flags")
                preferred_models = await matching_models(name, context.flags)
            
            if preferred_models is not None:
                if len(preferred_models) > 0:
                    context.data['model'] = preferred_models[0]

        if preferred_models is not None:
            if len(preferred_models) > 0:
                preferred_provider = preferred_models[0]['provider']

        print('name = ', name)
        if need_model:
            print('preferred models = ', preferred_models)
        function_info = None

        if not need_model and not preferred_provider:
            preferred_provider = self.functions[name][0]['provider']

        print(colored(f"need_model: {need_model}, preferred_provider: {preferred_provider}", "green"))

        if preferred_provider:
            for func_info in self.functions[name]:
                if func_info['provider'] == preferred_provider:
                    function_info = func_info
                    break

        if not function_info:
            raise ValueError(f"function '{name}' not found. preferred_provider is '{preferred_provider}'.")

        implementation = function_info['implementation']

        try:
            print(f"about to execute {name}, args= {args}, kwargs={kwargs}")
            try: 
                print(colored(f"model in context: {context.data['model']}", "cyan"))
                print(colored(f"provider: {function_info['provider']}", "green"))
            except:
                pass
                
            result = await implementation(*args, **kwargs)
        except Exception as e:
            raise e
        return result

    def get_docstring(self, name):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        return [func_info['docstring'] for func_info in self.functions[name]]

    def get_functions(self):
        return list(self.functions.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.functions.keys()}

    def get_some_docstrings(self, names):
        return {name: self.get_docstring(name) for name in names}

    def __getattr__(self, name):
        async def method(*args, **kwargs):
            print(f"method: {name} called")
            return await self.execute(name, *args, **kwargs)

        return method


import inspect

class HookManager:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, implementation, signature, docstring):
        if name not in self.hooks:
            self.hooks[name] = []
        self.hooks[name].append({
            'implementation': implementation,
            'docstring': docstring
        })

    async def execute_hooks(self, name, *args, **kwargs):
        if name not in self.hooks:
            return []
        results = []
        for hook_info in self.hooks[name]:
            implementation = hook_info['implementation']
            result = await implementation(*args, **kwargs)
            results.append(result)
        return results

    def get_docstring(self, name):
        if name not in self.hooks:
            raise ValueError(f"hook '{name}' not found.")
        return [hook_info['docstring'] for hook_info in self.hooks[name]]

    def get_hooks(self):
        return list(self.hooks.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.hooks.keys()}

    def __getattr__(self, name):
        async def method(*args, **kwargs):
            return await self.execute_hooks(name, *args, **kwargs)

        return method


