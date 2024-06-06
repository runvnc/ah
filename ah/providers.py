import inspect
import traceback

class ProviderManager:
    def __init__(self):
        self.functions = {}

    def register_function(self, name, implementation, signature, docstring, is_local=False):
        if name in self.functions:
            if name in self.functions and is_local in self.functions[name]:
        if name not in self.functions:
            self.functions[name] = {}

        self.functions[name][is_local] = {
            'implementation': implementation,
            'docstring': docstring,
            'is_local': is_local
        }

    async def execute(self, name, *args, **kwargs):
        prefer_local = True
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        local_function_info = self.functions[name].get(True)
        global_function_info = self.functions[name].get(False)
        function_info = None
        if prefer_local and local_function_info:
            function_info = local_function_info
        elif global_function_info:
            function_info = global_function_info
        else:
            function_info = local_function_info  # Fallback to local if global is not available
        
        found_context = False
        for arg in args:
            if arg.__class__.__name__ == 'ChatContext':
                found_context = True
                break
        
        if not found_context and not ('context' in kwargs):
            kwargs['context'] = self.context
        implementation = function_info['implementation']

        try:
            result = await implementation(*args, **kwargs)
        except Exception as e:
            raise e
        return result

    def get_docstring(self, name, prefer_local=False):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")

        docstring = None
        if prefer_local:
            if True in self.functions[name]:
                docstring = self.functions[name][True]['docstring']
        if not docstring:
            docstring = self.functions[name][False]['docstring']
        return docstring

    def get_functions(self):
        return list(self.functions.keys())

    def get_docstrings(self, prefer_local=True):
        return [self.get_docstring(name, prefer_local=prefer_local) for name in self.functions.keys()]

    def get_some_docstrings(self, names, prefer_local=True):
        return [self.get_docstring(name, prefer_local=prefer_local) for name in names]

    def is_local_function(self, name):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        return True in self.functions[name]

    def __getattr__(self, name):
        async def method(*args, **kwargs):
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


