#!/usr/bin/env python3
"""
基金经理分层监控体系
核心层(50人) + 重点层(200人) + 基础层(全市场异常监控)
"""

# 核心层：管理规模>100亿 + 业绩持续优秀（50人）
CORE_MANAGERS = [
    # 价值型（10人）
    {'name': '张坤', 'fund': '易方达蓝筹精选', 'code': '005827', 'company': '易方达', 'style': '深度价值', 'aum': '超800亿', 'tenure': '10年+'},
    {'name': '朱少醒', 'fund': '富国天惠成长', 'code': '161005', 'company': '富国', 'style': '均衡价值', 'aum': '超300亿', 'tenure': '15年+', 'return': '年化20%+'},
    {'name': '萧楠', 'fund': '易方达消费行业', 'code': '110022', 'company': '易方达', 'style': '消费价值', 'aum': '超300亿', 'tenure': '10年+'},
    {'name': '谢治宇', 'fund': '兴证全球合润', 'code': '163406', 'company': '兴证全球', 'style': '均衡价值', 'aum': '超600亿', 'tenure': '10年+'},
    {'name': '周蔚文', 'fund': '中欧新蓝筹', 'code': '166002', 'company': '中欧', 'style': '大盘价值', 'aum': '超500亿', 'tenure': '15年+'},
    {'name': '曹名长', 'fund': '中欧价值发现', 'code': '166005', 'company': '中欧', 'style': '深度价值', 'aum': '超100亿', 'tenure': '15年+', 'note': '深度价值老将'},
    {'name': '徐彦', 'fund': '大成策略回报', 'code': '090007', 'company': '大成', 'style': '逆向价值', 'aum': '超150亿', 'tenure': '10年+'},
    {'name': '丘栋荣', 'fund': '中庚价值领航', 'code': '006551', 'company': '中庚', 'style': '低估值价值', 'aum': '超200亿', 'tenure': '8年+', 'note': 'PB-ROE策略'},
    {'name': '姜诚', 'fund': '中泰星元价值优选', 'code': '006567', 'company': '中泰资管', 'style': '深度价值', 'aum': '超150亿', 'tenure': '6年+', 'note': '安全边际'},
    {'name': '谭丽', 'fund': '嘉实价值精选', 'code': '005267', 'company': '嘉实', 'style': '价值平衡', 'aum': '超200亿', 'tenure': '7年+'},
    
    # 成长型（15人）
    {'name': '葛兰', 'fund': '中欧医疗健康', 'code': '003095', 'company': '中欧', 'style': '医药成长', 'aum': '超600亿', 'tenure': '8年+', 'note': '医药女神'},
    {'name': '刘格菘', 'fund': '广发小盘成长', 'code': '162703', 'company': '广发', 'style': '科技成长', 'aum': '超600亿', 'tenure': '10年+', 'note': '2019年三冠王'},
    {'name': '冯明远', 'fund': '信达澳亚新能源', 'code': '001410', 'company': '信达澳亚', 'style': '硬科技成长', 'aum': '超200亿', 'tenure': '7年+', 'note': '科技猎手'},
    {'name': '赵诣', 'fund': '泉果旭源', 'code': '016709', 'company': '泉果', 'style': '新能源成长', 'aum': '超200亿', 'tenure': '6年+', 'note': '2020年四冠王'},
    {'name': '李晓星', 'fund': '银华中小盘精选', 'code': '180031', 'company': '银华', 'style': '成长均衡', 'aum': '超400亿', 'tenure': '8年+', 'note': '景气度投资'},
    {'name': '归凯', 'fund': '嘉实泰和', 'code': '000595', 'company': '嘉实', 'style': '质量成长', 'aum': '超300亿', 'tenure': '8年+'},
    {'name': '杨锐文', 'fund': '景顺长城优选', 'code': '260101', 'company': '景顺长城', 'style': '科技成长', 'aum': '超400亿', 'tenure': '9年+', 'note': '科技股投资'},
    {'name': '崔宸龙', 'fund': '前海开源公用事业', 'code': '005669', 'company': '前海开源', 'style': '新能源成长', 'aum': '超200亿', 'tenure': '4年+', 'note': '2021年双冠王'},
    {'name': '郑澄然', 'fund': '广发鑫享', 'code': '002132', 'company': '广发', 'style': '高端制造', 'aum': '超200亿', 'tenure': '4年+'},
    {'name': '陆彬', 'fund': '汇丰晋信低碳先锋', 'code': '540008', 'company': '汇丰晋信', 'style': '新能源成长', 'aum': '超200亿', 'tenure': '5年+'},
    {'name': '施成', 'fund': '国投瑞银新能源', 'code': '007689', 'company': '国投瑞银', 'style': '周期成长', 'aum': '超150亿', 'tenure': '5年+'},
    {'name': '韩创', 'fund': '大成新锐产业', 'code': '090018', 'company': '大成', 'style': '周期成长', 'aum': '超150亿', 'tenure': '5年+', 'note': '周期股专家'},
    {'name': '钟赟', 'fund': '南方新优享', 'code': '000527', 'company': '南方', 'style': '成长精选', 'aum': '超100亿', 'tenure': '6年+'},
    {'name': '王鹏', 'fund': '泰达宏利转型机遇', 'code': '000828', 'company': '泰达宏利', 'style': '景气成长', 'aum': '超100亿', 'tenure': '6年+'},
    {'name': '黄兴亮', 'fund': '万家行业优选', 'code': '161903', 'company': '万家', 'style': '科技成长', 'aum': '超100亿', 'tenure': '6年+'},
    
    # 均衡型（15人）
    {'name': '傅鹏博', 'fund': '睿远成长价值', 'code': '007119', 'company': '睿远', 'style': '逆向均衡', 'aum': '超200亿', 'tenure': '10年+', 'note': '老将'},
    {'name': '王崇', 'fund': '交银新成长', 'code': '519736', 'company': '交银施罗德', 'style': '稳健均衡', 'aum': '超200亿', 'tenure': '9年+', 'note': '回撤控制好'},
    {'name': '何帅', 'fund': '交银优势行业', 'code': '519697', 'company': '交银施罗德', 'style': '行业轮动', 'aum': '超150亿', 'tenure': '9年+'},
    {'name': '杨浩', 'fund': '交银定期支付双息平衡', 'code': '519732', 'company': '交银施罗德', 'style': '平衡策略', 'aum': '超100亿', 'tenure': '8年+'},
    {'name': '董承非', 'fund': '睿郡有孚', 'code': '私募', 'company': '睿郡', 'style': '逆向均衡', 'aum': '超100亿', 'tenure': '15年+', 'note': '奔私老将'},
    {'name': '周应波', 'fund': '运舟成长精选', 'code': '私募', 'company': '运舟', 'style': '成长均衡', 'aum': '超100亿', 'tenure': '8年+', 'note': '中欧前明星'},
    {'name': '刘旭', 'fund': '大成高新技术产业', 'code': '000628', 'company': '大成', 'style': '质量均衡', 'aum': '超100亿', 'tenure': '8年+'},
    {'name': '陈一峰', 'fund': '安信价值精选', 'code': '000577', 'company': '安信', 'style': '价值均衡', 'aum': '超100亿', 'tenure': '9年+'},
    {'name': '张清华', 'fund': '易方达安心回报', 'code': '110027', 'company': '易方达', 'style': '股债平衡', 'aum': '超600亿', 'tenure': '10年+', 'note': '固收+大佬'},
    {'name': '邬传雁', 'fund': '泓德远见回报', 'code': '001500', 'company': '泓德', 'style': '长期均衡', 'aum': '超200亿', 'tenure': '9年+'},
    {'name': '秦毅', 'fund': '泓德战略转型', 'code': '001705', 'company': '泓德', 'style': '价值均衡', 'aum': '超150亿', 'tenure': '7年+'},
    {'name': '于洋', 'fund': '富国新动力', 'code': '001508', 'company': '富国', 'style': '医药均衡', 'aum': '超100亿', 'tenure': '7年+'},
    {'name': '程洲', 'fund': '国泰聚信价值优势', 'code': '000362', 'company': '国泰', 'style': '逆向均衡', 'aum': '超100亿', 'tenure': '10年+'},
    {'name': '杜洋', 'fund': '工银战略转型', 'code': '000991', 'company': '工银瑞信', 'style': '大盘均衡', 'aum': '超150亿', 'tenure': '8年+'},
    {'name': '焦巍', 'fund': '银华富裕主题', 'code': '180012', 'company': '银华', 'style': '消费均衡', 'aum': '超200亿', 'tenure': '7年+'},
    
    # 行业主题型（10人）
    {'name': '蔡嵩松', 'fund': '诺安成长', 'code': '320007', 'company': '诺安', 'style': '半导体主题', 'aum': '超200亿', 'tenure': '5年+', 'note': '半导体一哥'},
    {'name': '郑巍山', 'fund': '银河创新成长', 'code': '519674', 'company': '银河', 'style': '科技主题', 'aum': '超150亿', 'tenure': '5年+'},
    {'name': '刘彦春', 'fund': '景顺长城新兴成长', 'code': '260108', 'company': '景顺长城', 'style': '消费主题', 'aum': '超500亿', 'tenure': '10年+', 'note': '消费天王'},
    {'name': '胡昕炜', 'fund': '汇添富消费行业', 'code': '000083', 'company': '汇添富', 'style': '消费主题', 'aum': '超300亿', 'tenure': '7年+'},
    {'name': '王宗合', 'fund': '鹏华消费优选', 'code': '206007', 'company': '鹏华', 'style': '消费主题', 'aum': '超200亿', 'tenure': '10年+'},
    {'name': '赵蓓', 'fund': '工银前沿医疗', 'code': '001717', 'company': '工银瑞信', 'style': '医药主题', 'aum': '超200亿', 'tenure': '8年+', 'note': '医药女神'},
    {'name': '楼慧源', 'fund': '交银医药创新', 'code': '004075', 'company': '交银施罗德', 'style': '医药主题', 'aum': '超100亿', 'tenure': '5年+'},
    {'name': '李瑞', 'fund': '东方新能源汽车', 'code': '400015', 'company': '东方', 'style': '新能源主题', 'aum': '超200亿', 'tenure': '6年+'},
    {'name': '姚志鹏', 'fund': '嘉实智能汽车', 'code': '002168', 'company': '嘉实', 'style': '智能汽车主题', 'aum': '超150亿', 'tenure': '7年+'},
    {'name': '李游', 'fund': '创金合信工业周期', 'code': '005968', 'company': '创金合信', 'style': '周期主题', 'aum': '超100亿', 'tenure': '6年+'},
]

# 重点层：管理规模30-100亿 + 某领域专长（200人框架）
KEY_MANAGERS_TEMPLATE = {
    '价值型': ['待补充40人'],
    '成长型': ['待补充50人'],
    '均衡型': ['待补充50人'],
    '行业主题': ['待补充40人'],
    '固收+': ['待补充20人']
}

# 监控配置
MONITOR_CONFIG = {
    'core_layer': {
        'count': 50,
        'report_depth': '九维度完整报告',
        'update_frequency': '季度',
        'data_sources': ['季报/年报', '访谈/路演', '直播', '社交媒体']
    },
    'key_layer': {
        'count': 200,
        'report_depth': '标准分析报告',
        'update_frequency': '季度',
        'data_sources': ['季报/年报', '访谈']
    },
    'base_layer': {
        'count': '全市场',
        'report_depth': '仅异常监控',
        'update_frequency': '半年度',
        'data_sources': ['季报关键指标'],
        'anomaly_triggers': ['业绩突变', '规模异动', '调仓异常', '人员变动']
    }
}

# 数据源配置
DATA_SOURCES = {
    'quarterly_report': {
        'name': '基金季报/年报',
        'url_pattern': 'https://fund.eastmoney.com/{code}.html',
        'update_frequency': '季度',
        'priority': 1
    },
    'company_website': {
        'name': '基金公司官网',
        'examples': ['https://www.efunds.com.cn', 'https://www.fsfund.com'],
        'update_frequency': '实时',
        'priority': 2
    },
    'interview': {
        'name': '访谈/路演',
        'platforms': ['蚂蚁财富', '天天基金', '雪球'],
        'update_frequency': '不定期',
        'priority': 3
    },
    'social_media': {
        'name': '社交媒体',
        'platforms': ['微博', '微信公众号'],
        'update_frequency': '实时',
        'priority': 4
    }
}

if __name__ == "__main__":
    print("="*70)
    print("基金经理分层监控体系 - 核心层名单")
    print("="*70)
    print()
    
    # 统计
    style_count = {}
    for m in CORE_MANAGERS:
        style = m['style']
        if '价值' in style:
            cat = '价值型'
        elif '成长' in style:
            cat = '成长型'
        elif '均衡' in style or '平衡' in style:
            cat = '均衡型'
        else:
            cat = '行业主题型'
        style_count[cat] = style_count.get(cat, 0) + 1
    
    print(f"核心层总人数: {len(CORE_MANAGERS)}人")
    print("风格分布:")
    for style, count in style_count.items():
        print(f"  - {style}: {count}人")
    print()
    
    print("Top 10 管理规模最大的基金经理:")
    sorted_managers = sorted(CORE_MANAGERS, 
                            key=lambda x: int(x['aum'].replace('超','').replace('亿','').replace('+','') or 0), 
                            reverse=True)[:10]
    for i, m in enumerate(sorted_managers, 1):
        print(f"{i}. {m['name']} ({m['company']}) - {m['aum']} - {m['fund']}")
    
    print()
    print("="*70)
    print("配置已就绪，可开始监控部署")
    print("="*70)
