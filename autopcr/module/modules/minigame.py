from typing import List, Set

from ...util.ilp_solver import memory_use_average

from ...model.common import ChangeRarityUnit, DeckListData, GachaPointInfo, GrandArenaHistoryDetailInfo, GrandArenaHistoryInfo, GrandArenaSearchOpponent, ProfileUserInfo, RankingSearchOpponent, RedeemUnitInfo, RedeemUnitSlotInfo, UnitData, UnitDataLight, VersusResult, VersusResultDetail
from ...model.responses import GachaIndexResponse, PsyTopResponse
from ...db.models import GachaExchangeLineup
from ...model.custom import ArenaQueryResult, GachaReward, ItemType, eRedeemUnitUnlockCondition
from ..modulebase import *
from ..config import *
from ...core.pcrclient import pcrclient
from ...core.apiclient import apiclient
from ...model.error import *
from ...db.database import db
from ...model.enums import *
import random
import itertools
from collections import Counter
import asyncio
from ...util.questutils import *

@description('剧情活动期间需首次击杀普通boss才能解锁该小游戏\n1.自动完成所有关卡\n2.一次最多刷200场对战，避免占用过多服务器资源\n3.每5场自动领取一次任务奖励 ')
@name('小游戏：激战！破坏！非法的战车大战')
@inttype("battle_count", "劲敌对战次数", 1, [i for i in range(0, 201)])
@default(True)
class mini_game_bsm(Module):
    async def do_task(self, client: pcrclient):
        battle_count: int = self.get_config('battle_count')

        try:
            res = await client.bsm_top(6001)
        except Exception as e:
            self._log(f"检查是否首通普通boss难度，当前无法获取小游戏信息: {e}")
            return
        await client.arcade_list(1014)
        await client.arcade_story(5156700)
        start_mode_id = res.last_clear_solo_mode_id + 1  # 从下一关开始
        
        for mode_id in range(start_mode_id, 51):  # 从已通关的下一关开始刷到第50关
            if mode_id == 12:  # 第12关需要阅读剧情
                await client.arcade_story(515671)
            
            token = create_battle_start_token()
            await client.bsm_solo_start(mode_id, 1, token, 6001)
            await client.bsm_solo_finish(3, token, 6001)
            self._log(f"战车大战第{mode_id}关完成")
        
        if battle_count > 0:
            for i in range(battle_count):  # 执行指定场次的对战
                await client.bsm_rival_battle_prepare(6001)
                token = create_battle_start_token()
                await client.bsm_battle_start(11, 0, 2, token, 6001)
                await client.bsm_battle_finish(3, token, 6001)
                if (i + 1) % 5 == 0:  # 每5场战斗检查一次，使用(i+1)确保在第5、10、15...场后执行
                    await client.bsm_mission_accept(0, 6001)

        res = await client.bsm_top(6001)
        self._log(f"对战{battle_count}场结束，当前pt点数：{res.battle_point}")
