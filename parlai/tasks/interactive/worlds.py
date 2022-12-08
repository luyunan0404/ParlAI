#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from copy import deepcopy

from typing import Optional
from parlai.core.opt import Opt

from parlai.core.params import ParlaiParser
from parlai.core.worlds import DialogPartnerWorld, validate
from parlai.core.message import Message


class InteractiveWorld(DialogPartnerWorld):
    """
    Simple interactive world involving just two agents talking.

    In more sophisticated worlds the environment could supply information, e.g. in
    tasks/convai2 both agents are given personas, so a world class should be written
    especially for those cases for given tasks.
    """

    @classmethod
    def add_cmdline_args(
        cls, parser: ParlaiParser, partial_opt: Optional[Opt] = None
    ) -> ParlaiParser:
        # no default args
        return parser

    def __init__(self, opt, agents, shared=None):
        super().__init__(opt, agents, shared)
        self.init_contexts(shared=shared)
        self.turn_cnt = 0
        self.first_time = True

    def init_contexts(self, shared=None):
        """
        Override to load or instantiate contexts to be used to seed the chat.
        """
        pass

    def get_contexts(self):
        """
        Override to return a pair of contexts with which to seed the episode.

        This function will be called before the first turn of every episode.
        """
        return ['', '']

    def finalize_episode(self):
        print("CHAT DONE ")
        if not self.epoch_done():
            print("\n... preparing new chat... \n")

    def parley(self):
        """
        Agent 0 goes first.
        [In our case, Agent 0 should be bot, Agent 1 should be human. So take out the first message from Agent0]
        [as the extra message and return it and from the next turn treat as the original case.]
        [In the original case, which can be seen from the parlai/scripts/interactive.py line:89
        human comes first]

        Alternate between the two agents.
        """

        acts = self.acts # list of two
        agents = self.agents # list of two agent objects

        if self.first_time:
            agents[0].observe(
                {
                    'id': 'World',
                    'text': 'Hello! This is Doctor bot to help you with your depression problem. Can you describe your situation?',
                }
            )
            self.first_time = False
            return

        try:
            act = deepcopy(agents[0].act(self.opt.get("is_chinese"))) #opt中的chinese作为local human的input传入
        except StopIteration:
            self.reset()
            self.finalize_episode()
            self.turn_cnt = 0
            return

        if not act:
            return

        act_text = act.get('text', None)

        acts[0] = act

        if act_text and '[DONE]' in act_text:
            agents[0].observe(validate(Message({'text': 'Goodbye!', 'episode_done': True})))
            self.reset()
            return

        # bot observe the human agent act(dict), the text from human is stored in act[0]["text"]
        agents[1].observe(validate(act))
        acts[1] = agents[1].act()
        print("bot act[1] is {}".format(acts[1]))
        agents[0].observe(validate(acts[1])) # human agent observe display the output from the bot act
        # the output from bot is acts[1]["text"]
        self.update_counters()
        self.turn_cnt += 1

        if act['episode_done']:
            self.finalize_episode()
            self.turn_cnt = 0
