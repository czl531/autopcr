from typing import Set
from ..modulebase import *
from ..config import *
from ...core.pcrclient import pcrclient
from ...model.error import *
from ...model.enums import *
from datetime import datetime
import json
from ...constants import DATA_DIR
import os
import os.path as path 
@description('刷新角色练度')
@name("刷新box")
@default(True)
class refresh_box(Module):
    async def do_task(self, client: pcrclient):
        self._log("刷新成功，当前box时间：" + db.format_time(datetime.fromtimestamp(client.data.data_time)))

@description('从缓存中查询角色练度，不会登录！任意登录或者刷新box可以更新缓存')
@name("查角色")
@default(True)
@notlogin(check_data=True)
@unitchoice("search_unit_id", "角色")
class search_unit(Module):
    async def do_task(self, client: pcrclient):
        unit_id = self.get_config('search_unit_id')
        unit = int(unit_id)
        unit_name = db.get_unit_name(unit)

        read_story = set(client.data.read_story_ids)
        info = [unit_id, unit_name]
        if unit not in client.data.unit:
            info += ['无'] * 7
        else:
            unitinfo = client.data.unit[unit]
            info.append(unitinfo.unit_rarity)
            info.append(unitinfo.unit_level)
            rank = f"r{unitinfo.promotion_level}"
            equip = ""
            for solt in unitinfo.equip_slot:
                equip += "-" if not solt.is_slot else str(solt.enhancement_level)
            info.append(f"{rank}({equip})")

            level = []
            level.append(unitinfo.union_burst[0].skill_level if unitinfo.union_burst else 0)
            level.append(unitinfo.main_skill[0].skill_level if unitinfo.main_skill else 0)
            level.append(unitinfo.main_skill[1].skill_level if len(unitinfo.main_skill) > 1 else 0)
            level.append(unitinfo.ex_skill[0].skill_level if unitinfo.ex_skill else 0)
            level = [str(i) for i in level]
            info.append('/'.join(level))

            read_storys = len([str(story.story_id) for story in db.unit_story if story.story_group_id == unit // 100 and story.story_id in read_story])
            not_read_storys = len([str(story.story_id) for story in db.unit_story if story.story_group_id == unit // 100 and story.story_id not in read_story])
            info.append("未实装" if not unitinfo.unique_equip_slot else "无" if not unitinfo.unique_equip_slot[0].is_slot else unitinfo.unique_equip_slot[0].enhancement_level)
            if len(unitinfo.unique_equip_slot) > 1:
                info.append("无" if not unitinfo.unique_equip_slot[1].is_slot else f"{unitinfo.unique_equip_slot[1].enhancement_level}星") 

            ex_equip = []
            for cb_ex in unitinfo.cb_ex_equip_slot:
                if not cb_ex.serial_id:
                    ex_equip.append("-")
                else:
                    ex = client.data.ex_equips[cb_ex.serial_id]
                    rarity = db.get_ex_equip_rarity_name(ex.ex_equipment_id)
                    star = db.get_ex_equip_star_from_pt(ex.ex_equipment_id, ex.enhancement_pt)
                    ex_equip.append(f"{rarity}{star}")
            info.append("/".join(i for i in ex_equip))

            kizuna_unit = set()
            for story in db.chara2story[unit]:
                if story.story_id in db.story_detail:
                    kizuna_unit.add(db.story_detail[story.story_id].requirement_id)

            love = []
            for other in kizuna_unit:
                if other not in db.unlock_unit_condition: continue
                kizuna_name = db.get_unit_name(other)
                unit_id = other // 100
                love_level = client.data.unit_love_data[unit_id].love_level if unit_id in client.data.unit_love_data else 0
                unit_story = [story.story_id for story in db.unit_story if story.story_group_id == unit_id]
                total_storys = len(unit_story)
                read_storys = len([story for story in unit_story if story in read_story])
                love.append(f"{kizuna_name}好感{love_level}({read_storys}/{total_storys})")
            info.append("\n" + ";".join(i for i in love))

        self._log(" ".join(str(i) for i in info))

        data = client.unit_info_to_dict(unit)
        header = ['姓名'] + list(data.keys())
        data.update({"姓名": unit_name})
        self._table_header(header)
        self._table(data)

# @description('从缓存中查询角色练度，不会登录！任意登录或者刷新box可以更新缓存')
# @name('查box')
# @notlogin(check_data=True)
# @default(True)
# @multichoice("box_talent_info", "属性信息", ['火深域', '水深域', '风深域', '光深域', '暗深域', '火属性', '水属性', '风属性', '光属性', '暗属性', '属性技能', '大师技能'], ['火深域', '水深域', '风深域', '光深域', '暗深域', '火属性', '水属性', '风属性', '光属性', '暗属性', '属性技能', '大师技能'])
# class get_box_table1(Module):
#     async def _prepare_user_data(self, client: pcrclient, user_info: Set[str]) -> Dict:
#         """准备用户基本信息"""
#         ret = {
#             "名字": client.data.user_name,
#         }
#         ret.update({
#             f"{db.talents[talent_id].talent_name}深域": client.data.get_talent_quest_single(talent_id) for talent_id in sorted([area.talent_id for area in db.talent_quest_area_data.values()])
#         })
#         ret.update({
#             f"{db.talents[talent_info.talent_id].talent_name}属性": client.data.get_talent_level_single(talent_info) for talent_info in client.data.princess_knight_info.talent_level_info_list
#         })
#         ret.update({
#             "属性技能": client.data.get_talent_skill_info(),
#             "大师技能": client.data.get_master_skill_info(),
#         })
#         ret = {key : ret[key] for key in ret if key in user_info}
#         print(ret)
#         return ret
# @description('包含uid、钻石、母猪石、心碎、星球杯等数据，不建议角色全部导出')
# @name('导出box练度excel')
# @notlogin(check_data=True)
# @default(True)
# @unitlist("export_units", "要导出的角色")
# class get_box_excel(BoxDataExportBase):
#     async def do_task(self, client: pcrclient):
#         # 处理过滤角色列表
#         export_units = self.get_config('export_units')
#         export_units = self._parse_unit_list(export_units)
        
#         # 筛选角色
#         filtered_units = self._get_filtered_units(client, export_units)
        
#         if not filtered_units:
#             raise AbortError("没有找到符合条件的角色")
        
#         # 准备数据
#         excel_data = {
#             "user_info": await self._prepare_user_data(client),
#             "units": []
#         }
        
#         # 添加角色信息
#         for unit in filtered_units:
#             unit_data = self._get_unit_data(client, unit)
#             excel_data["units"].append(unit_data)
        
#         # 将数据转换为JSON字符串并存入log
#         excel_json = json.dumps(excel_data, ensure_ascii=False)
#         self._log(f"BOX_EXCEL_DATA: {excel_json}")
#         self._log(f"共导出 {len(filtered_units)} 个角色的数据")


# @description('从缓存中查询角色练度，不会登录！任意登录或者刷新box可以更新缓存')
# @name('查box（多选）')
# @notlogin(check_data=True)
# @default(True)
# @unitlist("box_unit", "要显示的角色")
# @multichoice("box_user_info", "要显示的用户信息", [], ["UID", "数据时间", "钻石", "母猪石", "星球杯", "心碎"])
# class get_box_table(BoxDataExportBase):
#     async def do_task(self, client: pcrclient):
#         # 获取过滤角色列表
#         box_unit = self.get_config('box_unit')
#         box_unit = self._parse_unit_list(box_unit)
        
#         # 获取要显示的信息列
#         user_info = self.get_config('box_user_info')
        
#         # 筛选角色
#         filtered_units = self._get_filtered_units(client, box_unit)
        
#         if not filtered_units:
#             raise AbortError("没有找到符合条件的角色")

#         user_info = set(self.get_config('box_user_info')) | set(self.get_config('box_talent_info'))
#         box_unit_info = set(self.get_config('box_unit_info'))
        
#         header = []
#         data = {}

#         user_data = await self._prepare_user_data(client, user_info)
#         data.update(user_data)
#         header.extend(list(user_data.keys()))

#         for unit_id in filtered_units:
#             unit_data = self._get_unit_data(client, unit_id, box_unit_info)
#             unit_name = db.get_unit_name(unit_id)
#             header.append({unit_name: list(unit_data.keys())})
#             data[unit_name] = unit_data

#         self._table_header(header)
#         self._table(data)


class BoxDataExportBase(Module):
    async def _prepare_user_data(self, client: pcrclient):
        """准备用户基本信息"""
        return {
            "user_name": client.data.user_name,
            "user_id": client.data.uid,
            "jewel": client.data.jewel.free_jewel,
            "mother_stone": client.data.get_inventory((eInventoryType.Item, 90005)),
            "star_cup": client.data.get_inventory(db.xingqiubei),
            "heart_fragment": client.data.get_inventory(db.xinsui),
            "data_time": db.format_time(datetime.fromtimestamp(client.data.data_time))
        }
    
    def _parse_unit_list(self, unit_list):
        """解析角色列表，统一处理字符串和列表格式"""
        if isinstance(unit_list, str):
            try:
                try:
                    return json.loads(unit_list)
                except json.JSONDecodeError:
                    return [int(unit_id.strip()) for unit_id in unit_list.split(',') if unit_id.strip()]
            except Exception as e:
                self._log(f"解析角色列表出错: {e}")
                return [int(unit_id.strip()) for unit_id in unit_list.split(',') if unit_id.strip()]
        elif isinstance(unit_list, list):
            return [int(unit_id) if isinstance(unit_id, str) else unit_id for unit_id in unit_list]
        else:
            return []
    
    def _get_filtered_units(self, client: pcrclient, unit_list):
        """获取过滤后的角色列表"""
        filtered_units = []
        if unit_list:
            filtered_units = unit_list.copy()
            self._log(f"使用筛选角色列表，共{len(filtered_units)}个角色")
        else:
            filtered_units = list(client.data.unit.keys())
            self._log(f"使用所有角色，共{len(filtered_units)}个角色")
        return filtered_units
    
    def _get_unit_name(self, unit_id):
        """获取角色名称，优先使用昵称"""
        # 加载昵称文件
        try:
            nickname_json = os.path.join(DATA_DIR, 'nickname.json')
            if os.path.exists(nickname_json):
                with open(nickname_json, 'r', encoding='utf-8') as f:
                    nicknames = json.load(f)

                unit_id_str = str(unit_id)
                if unit_id_str in nicknames:
                    return nicknames[unit_id_str]
        except Exception as e:
            self._log(f"加载昵称文件出错: {e}")
        
        # 如果没有找到昵称或出错，使用默认名称
        return db.get_unit_name(unit_id)
    
    def _get_unit_data(self, client: pcrclient, unit_id: int):
        """获取单个角色的详细数据"""
        unit_data = {
            "unit_id": unit_id,
            "unit_name": self._get_unit_name(unit_id),  # 使用自定义的方法获取角色名
            "owned": unit_id in client.data.unit
        }
        
        if unit_id in client.data.unit:
            unitinfo = client.data.unit[unit_id]
            unit_data.update({
                "rarity": unitinfo.unit_rarity,
                "level": unitinfo.unit_level,
                "rank": unitinfo.promotion_level,
                "equip": "".join("-" if not slot.is_slot else str(slot.enhancement_level) for slot in unitinfo.equip_slot),
                "ub": unitinfo.union_burst[0].skill_level if unitinfo.union_burst else 0,
                "sk1": unitinfo.main_skill[0].skill_level if unitinfo.main_skill else 0,
                "sk2": unitinfo.main_skill[1].skill_level if len(unitinfo.main_skill) > 1 else 0,
                "ex": unitinfo.ex_skill[0].skill_level if unitinfo.ex_skill else 0,
                "unique_equip": "未实装" if not unitinfo.unique_equip_slot else 0 if not unitinfo.unique_equip_slot[0].is_slot else unitinfo.unique_equip_slot[0].enhancement_level,
                "unique_equip2": "未实装" if len(unitinfo.unique_equip_slot) < 2 else "-" if not unitinfo.unique_equip_slot[1].is_slot else unitinfo.unique_equip_slot[1].enhancement_level,
                "memory": client.data.get_inventory((eInventoryType.Item, db.unit_to_memory[unit_id])) if unit_id in db.unit_to_memory else "无",
                "pure_memory": client.data.get_inventory((eInventoryType.Item, db.unit_to_pure_memory[unit_id])) if unit_id in db.unit_to_pure_memory else "无",
            })
            
            # # 碎片数量
            # memory_count = 0
            # for memory_id, memory_unit_id in db.memory_to_unit.items():
            #     if memory_unit_id == unit_id:
            #         memory_count = client.data.get_inventory((eInventoryType.Item, memory_id))
            #         break
            # unit_data["memory"] = memory_count
            
            # # 金碎数量
            # pure_memory_count = 0
            # for pure_memory_item, pure_memory_unit_id in db.pure_memory_to_unit.items():
            #     if pure_memory_unit_id == unit_id:
            #         pure_memory_count = client.data.get_inventory(pure_memory_item)
            #         break
            # unit_data["pure_memory"] = pure_memory_count
        
        return unit_data
@description('包含uid、钻石、母猪石、心碎、星球杯等数据，不建议角色全部导出')
@name('导出box练度excel')
@notlogin(check_data=True)
@default(True)
@unitlist("export_units", "要导出的角色")
class get_box_excel(BoxDataExportBase):
    async def do_task(self, client: pcrclient):
        # 处理过滤角色列表
        export_units = self.get_config('export_units')
        export_units = self._parse_unit_list(export_units)
        
        # 筛选角色
        filtered_units = self._get_filtered_units(client, export_units)
        
        if not filtered_units:
            raise AbortError("没有找到符合条件的角色")
        
        # 准备数据
        excel_data = {
            "user_info": await self._prepare_user_data(client),
            "units": []
        }
        
        # 添加角色信息
        for unit in filtered_units:
            unit_data = self._get_unit_data(client, unit)
            excel_data["units"].append(unit_data)
        
        # 将数据转换为JSON字符串并存入log
        excel_json = json.dumps(excel_data, ensure_ascii=False)
        self._log(f"BOX_EXCEL_DATA: {excel_json}")
        self._log(f"共导出 {len(filtered_units)} 个角色的数据")


@description('从缓存中查询角色练度，不会登录！任意登录或者刷新box可以更新缓存')
@name('查box（多选）')
@notlogin(check_data=True)
@default(True)
@unitlist("box_unit", "要显示的角色")
@multichoice("box_user_info", "要显示的用户信息", [], ["UID", "数据时间", "钻石", "母猪石", "星球杯", "心碎"])
class get_box_table(BoxDataExportBase):
    async def do_task(self, client: pcrclient):
        # 获取过滤角色列表
        box_unit = self.get_config('box_unit')
        box_unit = self._parse_unit_list(box_unit)
        
        # 获取要显示的信息列
        user_info = self.get_config('box_user_info')
        
        # 筛选角色
        filtered_units = self._get_filtered_units(client, box_unit)
        
        if not filtered_units:
            raise AbortError("没有找到符合条件的角色")
        
        # 创建用户数据
        user_data = {
            "user_name": client.data.user_name,
            "user_info": user_info,
            "units": []
        }
        
        # 根据选择的信息列添加对应数据
        base_data = await self._prepare_user_data(client)
        if "UID" in user_info:
            user_data["uid"] = base_data["user_id"]
        if "数据时间" in user_info:
            user_data["data_time"] = base_data["data_time"]
        if "钻石" in user_info:
            user_data["jewel"] = base_data["jewel"]
        if "母猪石" in user_info:
            user_data["mother_stone"] = base_data["mother_stone"]
        if "星球杯" in user_info:
            user_data["star_cup"] = base_data["star_cup"]
        if "心碎" in user_info:
            user_data["heart_fragment"] = base_data["heart_fragment"]
        
        # 添加角色数据
        for unit_id in filtered_units:
            unit_data = self._get_unit_data(client, unit_id)
            user_data["units"].append(unit_data)
        
        # 将数据输出到日志中
        self._log(f"用户信息: {user_data['user_name']}")
        if "UID" in user_info:
            self._log(f"UID: {user_data.get('uid', '')}")
        if "数据时间" in user_info:
            self._log(f"数据时间: {user_data.get('data_time', '')}")
        if "钻石" in user_info:
            self._log(f"钻石: {user_data.get('jewel', '')}")
        if "母猪石" in user_info:
            self._log(f"母猪石: {user_data.get('mother_stone', '')}")
        if "星球杯" in user_info:
            self._log(f"星球杯: {user_data.get('star_cup', '')}")
        if "心碎" in user_info:
            self._log(f"心碎: {user_data.get('heart_fragment', '')}")
        self._log(f"角色数量: {len(user_data['units'])}")
        
        # 输出完整的JSON数据到日志
        self._log("BOX_DATA_START")
        self._log(json.dumps(user_data, ensure_ascii=False))
        self._log("BOX_DATA_END")
        
        self._log(f"已输出用户 {user_data['user_name']} 的角色练度数据")

@description('从缓存中查询属性练度，不会登录！任意登录或者刷新box可以更新缓存')
@name('查属性练度')
@notlogin(check_data=True)
@default(True)
class get_talent_info(Module):
    async def do_task(self, client: pcrclient):
        princess_knight_info = client.data.princess_knight_info
        
        if not princess_knight_info:
            self._log("未找到公主骑士信息")
            return

        # 显示属性等级信息
        talent_levels = {}
        for talent_info in princess_knight_info.talent_level_info_list:
            # talent_name = talent_names.get(talent_info.talent_id, f"属性{talent_info.talent_id}")
            current_level = db.get_talent_level(talent_info.total_point)
            
            # 获取对应属性未强化的点数
            unused_point_item_id = 25010 + talent_info.talent_id  # 25011 for fire, 25012 for water, etc.
            unused_points = client.data.get_inventory((eInventoryType.Item, unused_point_item_id))
            
            # 计算总点数和最高等级
            total_points = talent_info.total_point + unused_points
            max_level = db.get_talent_level(total_points)
            
            # 格式化为"当前等级【最高等级】"
            talent_levels[talent_info.talent_id] = f"{current_level}【{max_level}】"
        # 构造JSON格式的数据
        talent_enhance_info = {
            "talent_levels": talent_levels,
            "skill_tree": client.data.get_talent_skill_info(),
            "team_skill": client.data.get_master_skill_info(),
        }
        self._log(json.dumps(talent_enhance_info, ensure_ascii=False))
