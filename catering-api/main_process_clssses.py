def main_process_clssses(tree_struct: list, is_classic: bool, is_bbq: bool, is_children: bool, _headcount: str, _other: str, _cuisine: str) -> list:
    rtn_menu = []
    if is_classic:
        if len(_headcount) > 0:
            s_sublist = _headcount.split("|")
            for s_sub in s_sublist:
                if s_sub in tree_struct[0]["headcount"]:
                    rtn_menu.append(["经典到会", "按人数", s_sub])
            s_sublist = _other.split("|")
        if len(_other) > 0:
            for s_sub in s_sublist:
                if s_sub in tree_struct[0]["other"]:
                    rtn_menu.append(["经典到会", "按场景", s_sub])
            s_sublist = _cuisine.split("|")
        if len(_cuisine) > 0:
            for s_sub in s_sublist:
                if s_sub in tree_struct[0]["cuisine"]:
                    rtn_menu.append(["经典到会", "按菜式", s_sub])
    
    if is_bbq:
        if len(_headcount) > 0:
            s_sublist = _headcount.split("|")
            for s_sub in s_sublist:
                if s_sub in tree_struct[1]["headcount"]:
                    rtn_menu.append(["BBQ", "按人数", s_sub])
            s_sublist = _other.split("|")
        if len(_other) > 0:
            for s_sub in s_sublist:
                if s_sub in tree_struct[1]["other"]:
                    rtn_menu.append(["BBQ", "按场景", s_sub])
            s_sublist = _cuisine.split("|")
        if len(_cuisine) > 0:
            for s_sub in s_sublist:
                if s_sub in tree_struct[1]["cuisine"]:
                    rtn_menu.append(["BBQ", "按菜式", s_sub])
    
    if is_children:
        if len(_headcount) > 0:
            s_sublist = _headcount.split("|")
            for s_sub in s_sublist:
                if s_sub in tree_struct[2]["headcount"]:
                    rtn_menu.append(["小朋友生日", "按人数", s_sub])
            s_sublist = _other.split("|")
        if len(_other) > 0:
            for s_sub in s_sublist:
                if s_sub in tree_struct[2]["other"]:
                    rtn_menu.append(["小朋友生日", "按场景", s_sub])
            s_sublist = _cuisine.split("|")
        if len(_cuisine) > 0:
            for s_sub in s_sublist:
                if s_sub in tree_struct[2]["cuisine"]:
                    rtn_menu.append(["小朋友生日", "按菜式", s_sub])

    return rtn_menu


if __name__ == "__main__":
    tree_struct = [
        {
            "headcount": ["4-8人套餐", "10-15人套餐", "16-20人套餐", "21-25人套餐"],
            "other": ["家庭/公司聚餐", "派对Pizza 大食会", "早中午餐商务聚会", "轻食茶叙"],
            "cuisine": ["一人便当系列", "必选小食拼盘", "必食精选热盘", "头盘厨师沙律"]
        },
        {
            "headcount": ["4-8人套餐", "10-15人套餐", "16-20人套餐", "21-25人套餐"],
            "other": ["【食住烧】BBQ X到会套餐", "【超抵食】烧烤套餐", "【高级享受】烧烤套餐"],
            "cuisine": ["顶级牛", "滋味鸡扒", "惹味猪", "海鲜类"]
        },
        {
            "headcount": ["4-8人套餐", "10-15人套餐", "16-20人套餐", "21-25人套餐"],
            "other": ["繽紛花園仙子派對", "Peppa Pig 生日派對"]
        }
    ]
    rtn = main_process_clssses(tree_struct, True, False, False, "4-8人套餐", "家庭/公司聚餐|早中午餐商务聚会", "")
    print(rtn)
