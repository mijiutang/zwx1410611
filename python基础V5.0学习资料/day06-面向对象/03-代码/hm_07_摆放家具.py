class HouseItem:
    """家具类"""
    def __init__(self, name, area):
        self.name = name   # 名字
        self.area = area   # 占地面积

    def __str__(self):
        return f"{self.name} 占地面积 {self.area} 平米"


class House:
    """房子类"""
    def __init__(self, h_type, area):
        self.h_type = h_type    # 户型
        self.total_area = area  # 总面积
        self.free_area = area   # 剩余面积和总面积一样
        self.item_list = []     # 刚开始没有家具

    def __str__(self):
        return f"户型:{self.h_type}、总面积:{self.total_area} 平米、剩余面积:{self.free_area}平米、家具名称列表:{self.item_list}"

    def add_item(self, item):  # 1. 房子对象(self)   2. 家具对象(传参)
        """添加家具, item 家具对象"""
        # 1. 先判断房子的剩余面积和家具的占地面积的关系
        if self.free_area > item.area:  # 对象.属性  获取属性值
            print(f'添加家具: {item.name}')
            self.item_list.append(item.name)
            # 修改剩余面积
            self.free_area -= item.area
        else:
            print(f"房子剩余面积不足,换个大房子吧.....")


if __name__ == '__main__':
    # 创建家具对象
    bed = HouseItem('席梦思', 4)
    chest = HouseItem('衣柜', 2)
    table = HouseItem('餐桌', 1.5)
    print(bed)
    print(chest)
    print(table)
    # 创建房子
    house = House('三室一厅', 100)
    print(house)
    house.add_item(bed)
    print(house)
    house.add_item(chest)
    print(house)
    house.add_item(table)
    print(house)

