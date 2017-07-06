import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
from typing import List, Dict, Tuple

import neovim


MSG_PREFIX = '[Paiza] '
BASE_URL = 'http://api.paiza.io'


@neovim.plugin
class PaizaHandlers(object):

    def __init__(self, vim: neovim.api.Nvim):
        self._vim = vim  # type: neovim.api.Nvim

    @neovim.command('Paiza', range='%', nargs='*', complete='file')
    def command_handler(self, command_args: List[str], command_range):
        # TODO use range
        buf = self._vim.current.buffer[:]
        ft = self._vim.current.buffer.options['filetype']
        pwd = self._vim.command_output('pwd')[1:]
        code = '\n'.join(buf) + '\n'
        lang = ft_to_lang(ft)

        if len(command_args) > 1 and command_args[0] == '<':
            stdin_fname = command_args[1]

        self._vim.out_write(MSG_PREFIX + 'Executing code at paiza.io...\n')

        session_id, err = paiza_create_runner(code, lang)

        if err:
            self._vim.err_write(MSG_PREFIX + err + '\n')
            return

        # reserve get_status request
        self.start_timer(session_id)

    @neovim.function('_paiza_wait_loop')
    def wait_loop_handler(self, func_args: List[str]):
        session_id = func_args[0]
        status, err = paiza_get_status(session_id)
        if err:
            self._vim.err_write(MSG_PREFIX + err + '\n')
            return

        if status == 'running':
            # reserve next request
            self.start_timer(session_id)
        else:
            res = paiza_get_details(session_id)
            # TODO pretty output
            self._vim.out_write(json.dumps(res) + '\n')

    def start_timer(self, session_id: str):
        self._vim.eval(
            'timer_start(1000, {{-> execute("call _paiza_wait_loop(\'{0}\')")}})'
            .format(session_id))


def paiza_create_runner(code: str, lang: str, stdin: str=None) \
        -> Tuple[str, str]:
    dic = {'source_code': code, 'language': lang, 'api_key': 'guest'}
    if input:
        dic['input'] = stdin
    url = BASE_URL + '/runners/create?' + urlencode(dic)
    req = Request(url, method='POST')

    with urlopen(req) as f:
        # TODO net error handle
        res = json.load(f)

    return res.get('id'), res.get('error')

def paiza_get_status(session_id: str) -> Tuple[str, str]:
    dic = {'id': session_id, 'api_key': 'guest'}
    url = BASE_URL + '/runners/get_status?' + urlencode(dic)
    req = Request(url, method='GET')

    with urlopen(req) as f:
        # TODO net error handle
        res = json.load(f)

    return res.get('status'), res.get('error')

def paiza_get_details(session_id: str):
    dic = {'id': session_id, 'api_key': 'guest'}
    url = BASE_URL + '/runners/get_details?' + urlencode(dic)
    req = Request(url, method='GET')

    with urlopen(req) as f:
        # TODO net error handle
        res = json.load(f)

    return res

def ft_to_lang(ft: str) -> str:
    # TODO not implemented
    return ft
