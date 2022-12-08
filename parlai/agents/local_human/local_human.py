#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
"""
Agent does gets the local keyboard input in the act() function.

Example: parlai eval_model -m local_human -t babi:Task1k:1 -dt valid
"""

import json
import requests
from typing import Optional
from parlai.core.params import ParlaiParser
from parlai.core.opt import Opt
from parlai.core.agents import Agent
from parlai.core.message import Message
from parlai.utils.misc import display_messages, load_cands
from parlai.utils.strings import colorize
from parlai.utils import customize


class LocalHumanAgent(Agent):
    @classmethod
    def add_cmdline_args(
        cls, parser: ParlaiParser, partial_opt: Optional[Opt] = None
    ) -> ParlaiParser:
        """
        Add command-line arguments specifically for this agent.
        """
        agent = parser.add_argument_group('Local Human Arguments')
        agent.add_argument(
            '-fixedCands',
            '--local-human-candidates-file',
            default=None,
            type=str,
            help='File of label_candidates to send to other agent',
        )
        agent.add_argument(
            '--single_turn',
            type='bool',
            default=False,
            help='If on, assumes single turn episodes.',
        )
        return parser

    def __init__(self, opt, shared=None):
        super().__init__(opt)
        self.id = 'localHuman'
        self.episodeDone = False
        self.finished = False
        self.fixedCands_txt = load_cands(self.opt.get('local_human_candidates_file'))
        print(
            colorize(
                "Enter [DONE] if you want to end the episode, [EXIT] to quit.",
                'highlight',
            )
        )

    def epoch_done(self):
        return self.finished

    def observe(self, msg):
        print(
            display_messages(
                [msg],
                add_fields=self.opt.get('display_add_fields', ''),
                prettify=self.opt.get('display_prettify', False),
                verbose=self.opt.get('verbose', False),
                is_chinese=self.opt.get("is_chinese"),
                id_file_path=self.opt.get("id_file_path")
            )
        )

    def get_token(self):

        url = "https://api.alefcloud.cn/api/auth/jwt/apiToken"

        payload = json.dumps({
            "username": "admin",
            "password": "admin"
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        return response

    def translate(self, token, input_text=None, from_lang="zh-cn", to_lang="en"):
        url = "https://api.alefcloud.cn/api/translate/getTranslateResultPost"

        payload = {
            'text': input_text,
            'fromLang': from_lang,
            'toLang': to_lang,
            'model': '0'}
        headers = {
            'Authorization': token
        }

        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        return response

    def act(self, is_chinese=False):
        reply = Message()
        reply['id'] = self.getID()
        try:
            print(is_chinese)
            if not is_chinese:
                reply_text = input(colorize("Enter Your Message:", 'text') + ' ')
            else:
                chinese_input = input(colorize("Enter Your Message:", 'text') + ' ')
                id_file_path = self.opt.get("id_file_path")
                chinese_input = customize.translate_personal(id_file_path, chinese_input, from_lang="zh-cn", to_lang="en")
                token_response = self.get_token()
                token = token_response.json().get("data").get("accessToken")
                translate_response = self.translate(token, input_text=chinese_input)
                reply_text = translate_response.json().get("data")
                print(reply_text)
        except EOFError:
            self.finished = True
            return {'episode_done': True}

        reply_text = reply_text.replace('\\n', '\n')
        reply['episode_done'] = False
        if self.opt.get('single_turn', False):
            reply.force_set('episode_done', True)
        reply['label_candidates'] = self.fixedCands_txt
        if '[DONE]' in reply_text:
            # let interactive know we're resetting
            raise StopIteration
        reply['text'] = reply_text
        if '[EXIT]' in reply_text:
            self.finished = True
            raise StopIteration
        return reply

    def episode_done(self):
        return self.episodeDone
