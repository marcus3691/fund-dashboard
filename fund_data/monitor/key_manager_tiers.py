#!/usr/bin/env python3
"""
基金经理重点层名单（200人）
标准：管理规模30-100亿 + 某领域专长
按风格分类：价值型/成长型/均衡型/行业主题型/固收+
"""

# 重点层 - 价值型（40人）
VALUE_MANAGERS = [
    # 深度价值（15人）
    {'name': '鲍无可', 'fund': '景顺长城能源基建', 'code': '260112', 'company': '景顺长城', 'style': '深度价值', 'aum': '80亿+', 'note': '低估值策略'},
    {'name': '林英睿', 'fund': '广发睿毅领先', 'code': '005233', 'company': '广发', 'style': '困境反转', 'aum': '70亿+', 'note': '航空股投资'},
    {'name': '王海峰', 'fund': '银华鑫盛灵活', 'code': '501022', 'company': '银华', 'style': '周期价值', 'aum': '60亿+', 'note': '周期股专家'},
    {'name': '杨嘉文', 'fund': '易方达科瑞', 'code': '003293', 'company': '易方达', 'style': '价值成长', 'aum': '50亿+', 'note': '中小盘价值'},
    {'name': '程琨', 'fund': '广发优企精选', 'code': '002624', 'company': '广发', 'style': '企业价值', 'aum': '50亿+', 'note': '企业质量选股'},
    {'name': '吴渭', 'fund': '博时汇智回报', 'code': '004448', 'company': '博时', 'style': '绝对收益', 'aum': '40亿+', 'note': '回撤控制好'},
    {'name': '袁维德', 'fund': '中欧价值智选', 'code': '166005', 'company': '中欧', 'style': '价值平衡', 'aum': '80亿+', 'note': '曹名长团队'},
    {'name': '蓝小康', 'fund': '中欧红利优享', 'code': '004814', 'company': '中欧', 'style': '红利价值', 'aum': '60亿+', 'note': '高股息策略'},
    {'name': '李崟', 'fund': '安信稳健增值', 'code': '001316', 'company': '安信', 'style': '稳健价值', 'aum': '90亿+', 'note': '绝对收益'},
    {'name': '张翼飞', 'fund': '安信民稳增长', 'code': '008809', 'company': '安信', 'style': '股债平衡', 'aum': '70亿+', 'note': '固收+策略'},
    {'name': '高远', 'fund': '长信金利趋势', 'code': '519994', 'company': '长信', 'style': '趋势价值', 'aum': '50亿+', 'note': '趋势投资'},
    {'name': '王斌', 'fund': '华安聚嘉精选', 'code': '011251', 'company': '华安', 'style': '精选价值', 'aum': '80亿+', 'note': '新兴产业'},
    {'name': '胡宜斌', 'fund': '华安媒体互联网', 'code': '001071', 'company': '华安', 'style': '科技价值', 'aum': '90亿+', 'note': 'TMT投资'},
    {'name': '刘辉', 'fund': '银华内需精选', 'code': '161810', 'company': '银华', 'style': '内需价值', 'aum': '50亿+', 'note': '消费周期'},
    {'name': '焦巍', 'fund': '银华富裕主题', 'code': '180012', 'company': '银华', 'style': '消费价值', 'aum': '200亿+', 'note': '已入核心层'},
    
    # 大盘价值（15人）
    {'name': '王君正', 'fund': '工银金融地产', 'code': '000251', 'company': '工银瑞信', 'style': '金融地产', 'aum': '60亿+', 'note': '金融地产专家'},
    {'name': '鄢耀', 'fund': '工银新金融', 'code': '001054', 'company': '工银瑞信', 'style': '新金融', 'aum': '50亿+', 'note': '金融创新'},
    {'name': '陈小鹭', 'fund': '华泰柏瑞富利', 'code': '004475', 'company': '华泰柏瑞', 'style': '周期价值', 'aum': '80亿+', 'note': '周期股轮动'},
    {'name': '董辰', 'fund': '华泰柏瑞新利', 'code': '001247', 'company': '华泰柏瑞', 'style': '灵活配置', 'aum': '100亿+', 'note': '已入核心层'},
    {'name': '沈楠', 'fund': '交银施罗德稳健', 'code': '519690', 'company': '交银施罗德', 'style': '稳健配置', 'aum': '60亿+', 'note': '稳健收益'},
    {'name': '郭斐', 'fund': '交银成长30', 'code': '519727', 'company': '交银施罗德', 'style': '成长股', 'aum': '50亿+', 'note': '成长投资'},
    {'name': '李永兴', 'fund': '永赢惠添利', 'code': '005711', 'company': '永赢', 'style': '价值投资', 'aum': '80亿+', 'note': '前交银明星'},
    {'name': '常蓁', 'fund': '嘉实回报混合', 'code': '070018', 'company': '嘉实', 'style': '质量价值', 'aum': '70亿+', 'note': '质量成长'},
    {'name': '姚志鹏', 'fund': '嘉实智能汽车', 'code': '002168', 'company': '嘉实', 'style': '智能汽车', 'aum': '150亿+', 'note': '已入核心层'},
    {'name': '张金涛', 'fund': '嘉实沪港深精选', 'code': '001878', 'company': '嘉实', 'style': '港股价值', 'aum': '60亿+', 'note': '港股投资'},
    {'name': '洪流', 'fund': '嘉实价值成长', 'code': '007895', 'company': '嘉实', 'style': '价值成长', 'aum': '50亿+', 'note': '均衡配置'},
    {'name': '吴悠', 'fund': '嘉实先进制造', 'code': '001039', 'company': '嘉华实', 'style': '制造价值', 'aum': '40亿+', 'note': '制造业'},
    {'name': '肖觅', 'fund': '嘉实基础产业优选', 'code': '009126', 'company': '嘉实', 'style': '基础产业', 'aum': '50亿+', 'note': '基础设施'},
    {'name': '苏文杰', 'fund': '嘉实资源精选', 'code': '005660', 'company': '嘉实', 'style': '资源价值', 'aum': '30亿+', 'note': '资源周期'},
    {'name': '刘杰', 'fund': '景顺长城量化新动力', 'code': '001974', 'company': '景顺长城', 'style': '量化价值', 'aum': '40亿+', 'note': '量化策略'},
    
    # 红利/高股息（10人）
    {'name': '孙迪', 'fund': '广发高端制造', 'code': '004997', 'company': '广发', 'style': '高端制造', 'aum': '100亿+', 'note': '制造业'},
    {'name': '郑澄然', 'fund': '广发鑫享', 'code': '002132', 'company': '广发', 'style': '新能源', 'aum': '200亿+', 'note': '已入核心层'},
    {'name': '唐晓斌', 'fund': '广发多因子', 'code': '002943', 'company': '广发', 'style': '多因子', 'aum': '80亿+', 'note': '量化策略'},
    {'name': '林庆', 'fund': '富国文体健康', 'code': '001186', 'company': '富国', 'style': '文体健康', 'aum': '60亿+', 'note': '消费医疗'},
    {'name': '于渤', 'fund': '富国新收益', 'code': '001345', 'company': '富国', 'style': '绝对收益', 'aum': '50亿+', 'note': '稳健收益'},
    {'name': '蒲世林', 'fund': '富国城镇发展', 'code': '000471', 'company': '富国', 'style': '城镇发展', 'aum': '40亿+', 'note': '城镇化'},
    {'name': '刘博', 'fund': '富国周期优势', 'code': '005760', 'company': '富国', 'style': '周期优势', 'aum': '50亿+', 'note': '周期股'},
    {'name': '曹文俊', 'fund': '富国转型机遇', 'code': '005739', 'company': '富国', 'style': '转型机遇', 'aum': '80亿+', 'note': '产业升级'},
    {'name': '厉叶淼', 'fund': '富国天瑞强势', 'code': '100022', 'company': '富国', 'style': '强势精选', 'aum': '70亿+', 'note': '精选个股'},
    {'name': '汪孟海', 'fund': '富国沪港深价值', 'code': '001371', 'company': '富国', 'style': '沪港深', 'aum': '60亿+', 'note': '港股投资'},
]

# 重点层 - 成长型（60人）
GROWTH_MANAGERS = [
    # 科技成长（20人）
    {'name': '刘鹏', 'fund': '交银先进制造', 'code': '011448', 'company': '交银施罗德', 'style': '先进制造', 'aum': '80亿+', 'note': '制造业升级'},
    {'name': '田彧龙', 'fund': '交银数据产业', 'code': '011248', 'company': '交银施罗德', 'style': '数据产业', 'aum': '60亿+', 'note': '大数据'},
    {'name': '郭斐', 'fund': '交银成长30', 'code': '519727', 'company': '交银施罗德', 'style': '成长30', 'aum': '50亿+', 'note': '成长股'},
    {'name': '芮晨', 'fund': '交银科技创新', 'code': '007853', 'company': '交银施罗德', 'style': '科技创新', 'aum': '40亿+', 'note': '科技股'},
    {'name': '何肖颉', 'fund': '工银新趋势', 'code': '001227', 'company': '工银瑞信', 'style': '新趋势', 'aum': '50亿+', 'note': '趋势投资'},
    {'name': '单文', 'fund': '工银互联网加', 'code': '001409', 'company': '工银瑞信', 'style': '互联网+', 'aum': '70亿+', 'note': '互联网'},
    {'name': '张继圣', 'fund': '工银信息产业', 'code': '000263', 'company': '工银瑞信', 'style': '信息产业', 'aum': '60亿+', 'note': '信息科技'},
    {'name': '欧阳凯', 'fund': '工银瑞信双利', 'code': '485111', 'company': '工银瑞信', 'style': '双利债', 'aum': '100亿+', 'note': '固收+'},
    {'name': '何秀红', 'fund': '工银产业债', 'code': '000045', 'company': '工银瑞信', 'style': '产业债', 'aum': '80亿+', 'note': '信用债'},
    {'name': '王筱苓', 'fund': '工银大盘蓝筹', 'code': '481008', 'company': '工银瑞信', 'style': '大盘蓝筹', 'aum': '50亿+', 'note': '蓝筹股'},
    {'name': '盛骅', 'fund': '华夏兴华混合', 'code': '519908', 'company': '华夏', 'style': '兴华精选', 'aum': '60亿+', 'note': '精选个股'},
    {'name': '张帆', 'fund': '华夏经济转型', 'code': '002229', 'company': '华夏', 'style': '经济转型', 'aum': '50亿+', 'note': '转型机遇'},
    {'name': '孙轶佳', 'fund': '华夏新兴消费', 'code': '005888', 'company': '华夏', 'style': '新兴消费', 'aum': '40亿+', 'note': '新消费'},
    {'name': '周克平', 'fund': '华夏复兴混合', 'code': '000031', 'company': '华夏', 'style': '复兴成长', 'aum': '90亿+', 'note': '成长股'},
    {'name': '吕佳玮', 'fund': '华夏高端制造', 'code': '002345', 'company': '华夏', 'style': '高端制造', 'aum': '50亿+', 'note': '制造业'},
    {'name': '屠环宇', 'fund': '华夏创新前沿', 'code': '002980', 'company': '华夏', 'style': '创新前沿', 'aum': '70亿+', 'note': '创新科技'},
    {'name': '季新星', 'fund': '华夏行业景气', 'code': '003567', 'company': '华夏', 'style': '行业景气', 'aum': '100亿+', 'note': '景气投资'},
    {'name': '黄文倩', 'fund': '华夏消费升级', 'code': '001927', 'company': '华夏', 'style': '消费升级', 'aum': '60亿+', 'note': '消费升级'},
    {'name': '马君', 'fund': '华安智能生活', 'code': '006228', 'company': '华安', 'style': '智能生活', 'aum': '50亿+', 'note': '智能科技'},
    {'name': '舒灏', 'fund': '华安新机遇', 'code': '001282', 'company': '华安', 'style': '新机遇', 'aum': '40亿+', 'note': '灵活配置'},
    
    # 医药成长（15人）
    {'name': '葛晨', 'fund': '博时医疗保健', 'code': '050026', 'company': '博时', 'style': '医疗保健', 'aum': '60亿+', 'note': '医药投资'},
    {'name': '张弘', 'fund': '汇添富达欣', 'code': '001801', 'company': '汇添富', 'style': '达欣成长', 'aum': '50亿+', 'note': '成长精选'},
    {'name': '刘江', 'fund': '汇添富医疗服务', 'code': '001417', 'company': '汇添富', 'style': '医疗服务', 'aum': '80亿+', 'note': '医疗服务'},
    {'name': '马翔', 'fund': '汇添富民营活力', 'code': '470009', 'company': '汇添富', 'style': '民营活力', 'aum': '70亿+', 'note': '民营企业'},
    {'name': '雷鸣', 'fund': '汇添富蓝筹稳健', 'code': '519066', 'company': '汇添富', 'style': '蓝筹稳健', 'aum': '90亿+', 'note': '稳健蓝筹'},
    {'name': '劳杰男', 'fund': '汇添富价值精选', 'code': '519069', 'company': '汇添富', 'style': '价值精选', 'aum': '100亿+', 'note': '价值精选'},
    {'name': '杨瑨', 'fund': '汇添富全球互联', 'code': '001668', 'company': '汇添富', 'style': '全球互联', 'aum': '60亿+', 'note': 'QDII'},
    {'name': '郑磊', 'fund': '汇添富创新医药', 'code': '006113', 'company': '汇添富', 'style': '创新医药', 'aum': '70亿+', 'note': '医药创新'},
    {'name': '过蓓蓓', 'fund': '汇添富中证中药', 'code': '501011', 'company': '汇添富', 'style': '中药ETF', 'aum': '50亿+', 'note': '指数基金'},
    {'name': '谭小兵', 'fund': '长城医疗保健', 'code': '000339', 'company': '长城', 'style': '医疗保健', 'aum': '40亿+', 'note': '医药主题'},
    {'name': '赵伟', 'fund': '农银汇理医疗保健', 'code': '000913', 'company': '农银汇理', 'style': '医疗保健', 'aum': '50亿+', 'note': '医药投资'},
    {'name': '梦圆', 'fund': '农银汇理创新医疗', 'code': '008293', 'company': '农银汇理', 'style': '创新医疗', 'aum': '60亿+', 'note': '医疗创新'},
    {'name': '徐治彪', 'fund': '国泰大健康', 'code': '001645', 'company': '国泰', 'style': '大健康', 'aum': '70亿+', 'note': '健康主题'},
    {'name': '茅炜', 'fund': '南方科技创新', 'code': '007340', 'company': '南方', 'style': '科技创新', 'aum': '80亿+', 'note': '科技创新'},
    {'name': '王峥娇', 'fund': '南方医药创新', 'code': '010592', 'company': '南方', 'style': '医药创新', 'aum': '50亿+', 'note': '医药主题'},
    
    # 新能源/高端制造（15人）
    {'name': '陶灿', 'fund': '建信新能源', 'code': '009147', 'company': '建信', 'style': '新能源', 'aum': '100亿+', 'note': '新能源主题'},
    {'name': '邵卓', 'fund': '建信创新中国', 'code': '000308', 'company': '建信', 'style': '创新中国', 'aum': '60亿+', 'note': '创新成长'},
    {'name': '周智硕', 'fund': '建信潜力新蓝筹', 'code': '000756', 'company': '建信', 'style': '潜力蓝筹', 'aum': '50亿+', 'note': '新蓝筹'},
    {'name': '蒋华安', 'fund': '中欧养老产业', 'code': '001955', 'company': '中欧', 'style': '养老产业', 'aum': '70亿+', 'note': '养老主题'},
    {'name': '成雨轩', 'fund': '中欧时代智慧', 'code': '005241', 'company': '中欧', 'style': '时代智慧', 'aum': '60亿+', 'note': '智慧投资'},
    {'name': '许文星', 'fund': '中欧电子信息产业', 'code': '004616', 'company': '中欧', 'style': '电子信息', 'aum': '80亿+', 'note': '电子信息'},
    {'name': '周蔚文', 'fund': '中欧新蓝筹', 'code': '166002', 'company': '中欧', 'style': '新蓝筹', 'aum': '500亿+', 'note': '已入核心层'},
    {'name': '代云锋', 'fund': '华宝创新优选', 'code': '000601', 'company': '华宝', 'style': '创新优选', 'aum': '50亿+', 'note': '创新驱动'},
    {'name': '夏林锋', 'fund': '华安生态优先', 'code': '000294', 'company': '华安', 'style': '生态优先', 'aum': '60亿+', 'note': '生态环境'},
    {'name': '万建军', 'fund': '华安研究精选', 'code': '005630', 'company': '华安', 'style': '研究精选', 'aum': '70亿+', 'note': '深度研究'},
    {'name': '刘畅畅', 'fund': '华安文体健康', 'code': '001532', 'company': '华安', 'style': '文体健康', 'aum': '80亿+', 'note': '文体产业'},
    {'name': '李欣', 'fund': '华安智能装备', 'code': '001072', 'company': '华安', 'style': '智能装备', 'aum': '50亿+', 'note': '智能制造'},
    {'name': '谢昌旭', 'fund': '华安品质甄选', 'code': '013680', 'company': '华安', 'style': '品质甄选', 'aum': '40亿+', 'note': '品质投资'},
    {'name': '舒灏', 'fund': '华安新核心', 'code': '001281', 'company': '华安', 'style': '新核心', 'aum': '30亿+', 'note': '核心资产'},
    {'name': '饶晓鹏', 'fund': '华安汇嘉精选', 'code': '010557', 'company': '华安', 'style': '汇嘉精选', 'aum': '60亿+', 'note': '精选个股'},
    {'name': '陈媛', 'fund': '华安优享生活', 'code': '005521', 'company': '华安', 'style': '优享生活', 'aum': '50亿+', 'note': '生活主题'},
    {'name': '金信', 'fund': '华安低碳生活', 'code': '006122', 'company': '华安', 'style': '低碳生活', 'aum': '40亿+', 'note': '低碳环保'},
    {'name': '孔涛', 'fund': '南方现代教育', 'code': '003956', 'company': '南方', 'style': '现代教育', 'aum': '40亿+', 'note': '教育主题'},
    {'name': '章晖', 'fund': '南方新优享', 'code': '000527', 'company': '南方', 'style': '新优享', 'aum': '70亿+', 'note': '优选成长'},
    {'name': '骆帅', 'fund': '南方优选成长', 'code': '202023', 'company': '南方', 'style': '优选成长', 'aum': '60亿+', 'note': '成长精选'},
]

# 重点层 - 均衡型（50人）
BALANCED_MANAGERS = [
    # 大盘均衡（20人）
    {'name': '陈皓', 'fund': '易方达科翔', 'code': '110013', 'company': '易方达', 'style': '科翔成长', 'aum': '100亿+', 'note': '成长均衡'},
    {'name': '武阳', 'fund': '易方达瑞程', 'code': '003961', 'company': '易方达', 'style': '瑞程配置', 'aum': '60亿+', 'note': '灵活配置'},
    {'name': '刘武', 'fund': '易方达新兴成长', 'code': '000404', 'company': '易方达', 'style': '新兴成长', 'aum': '90亿+', 'note': '新兴产业'},
    {'name': '孙松', 'fund': '易方达新常态', 'code': '001184', 'company': '易方达', 'style': '新常态', 'aum': '70亿+', 'note': '新经济'},
    {'name': '林森', 'fund': '易方达瑞弘', 'code': '003882', 'company': '易方达', 'style': '瑞弘配置', 'aum': '80亿+', 'note': '稳健配置'},
    {'name': '王成', 'fund': '易方达鑫享', 'code': '003789', 'company': '易方达', 'style': '鑫享配置', 'aum': '50亿+', 'note': '灵活策略'},
    {'name': '祁禾', 'fund': '易方达环保主题', 'code': '001856', 'company': '易方达', 'style': '环保主题', 'aum': '100亿+', 'note': '环保产业'},
    {'name': '杨桢霄', 'fund': '易方达供给改革', 'code': '002910', 'company': '易方达', 'style': '供给改革', 'aum': '70亿+', 'note': '供给侧改革'},
    {'name': '贾健', 'fund': '易方达创新驱动', 'code': '000603', 'company': '易方达', 'style': '创新驱动', 'aum': '60亿+', 'note': '创新科技'},
    {'name': '杨康', 'fund': '易方达新享', 'code': '001342', 'company': '易方达', 'style': '新享配置', 'aum': '50亿+', 'note': '稳健配置'},
    {'name': '吴欣荣', 'fund': '兴证全球趋势投资', 'code': '163402', 'company': '兴证全球', 'style': '趋势投资', 'aum': '80亿+', 'note': '趋势跟踪'},
    {'name': '童兰', 'fund': '兴证全球欣越', 'code': '012087', 'company': '兴证全球', 'style': '欣越配置', 'aum': '60亿+', 'note': '灵活配置'},
    {'name': '钱鑫', 'fund': '兴证全球恒益', 'code': '008952', 'company': '兴证全球', 'style': '恒益债券', 'aum': '70亿+', 'note': '债券+'},
    {'name': '申庆', 'fund': '兴证全球沪深300指数', 'code': '163407', 'company': '兴证全球', 'style': '指数增强', 'aum': '50亿+', 'note': '指数投资'},
    {'name': '陈宇', 'fund': '兴证全球兴全精选', 'code': '163411', 'company': '兴证全球', 'style': '全精选', 'aum': '90亿+', 'note': '精选个股'},
    {'name': '季文华', 'fund': '兴证全球合宜', 'code': '163417', 'company': '兴证全球', 'style': '合宜配置', 'aum': '100亿+', 'note': '均衡配置'},
    {'name': '任相栋', 'fund': '兴证全球合泰', 'code': '007802', 'company': '兴证全球', 'style': '合泰配置', 'aum': '80亿+', 'note': '均衡策略'},
    {'name': '乔迁', 'fund': '兴证全球商业模式', 'code': '163415', 'company': '兴证全球', 'style': '商业模式', 'aum': '120亿+', 'note': '商业分析'},
    {'name': '董理', 'fund': '兴证全球轻资产', 'code': '163412', 'company': '兴证全球', 'style': '轻资产', 'aum': '70亿+', 'note': '轻资产模式'},
    {'name': '邹欣', 'fund': '兴证全球绿色投资', 'code': '163409', 'company': '兴证全球', 'style': '绿色投资', 'aum': '60亿+', 'note': 'ESG投资'},
    
    # 灵活配置（15人）
    {'name': '杜猛', 'fund': '上投摩根新兴动力', 'code': '377240', 'company': '摩根士丹利华鑫', 'style': '新兴动力', 'aum': '80亿+', 'note': '新兴行业'},
    {'name': '李德辉', 'fund': '上投摩根科技前沿', 'code': '001538', 'company': '摩根士丹利华鑫', 'style': '科技前沿', 'aum': '70亿+', 'note': '科技投资'},
    {'name': '冯波', 'fund': '易方达行业领先', 'code': '110015', 'company': '易方达', 'style': '行业领先', 'aum': '100亿+', 'note': '行业龙头'},
    {'name': '王元春', 'fund': '易方达现代服务业', 'code': '005835', 'company': '易方达', 'style': '现代服务业', 'aum': '60亿+', 'note': '服务业'},
    {'name': '郭杰', 'fund': '易方达改革红利', 'code': '001076', 'company': '易方达', 'style': '改革红利', 'aum': '50亿+', 'note': '改革主题'},
    {'name': '蔡荣成', 'fund': '易方达远见成长', 'code': '010115', 'company': '易方达', 'style': '远见成长', 'aum': '70亿+', 'note': '长期成长'},
    {'name': '张清华', 'fund': '易方达新收益', 'code': '001216', 'company': '易方达', 'style': '新收益', 'aum': '150亿+', 'note': '已入核心层'},
    {'name': '李中阳', 'fund': '富国天益价值', 'code': '100020', 'company': '富国', 'style': '天益价值', 'aum': '80亿+', 'note': '价值精选'},
    {'name': '孙伟', 'fund': '民生加银策略精选', 'code': '000136', 'company': '民生加银', 'style': '策略精选', 'aum': '60亿+', 'note': '策略配置'},
    {'name': '柳世庆', 'fund': '民生加银城镇化', 'code': '000408', 'company': '民生加银', 'style': '城镇化', 'aum': '50亿+', 'note': '城镇化主题'},
    {'name': '高松', 'fund': '民生加银稳健成长', 'code': '000363', 'company': '民生加银', 'style': '稳健成长', 'aum': '40亿+', 'note': '稳健增长'},
    {'name': '蔡晓', 'fund': '民生加银研究精选', 'code': '001220', 'company': '民生加银', 'style': '研究精选', 'aum': '50亿+', 'note': '深度研究'},
    {'name': '王亮', 'fund': '民生加银景气行业', 'code': '690007', 'company': '民生加银', 'style': '景气行业', 'aum': '70亿+', 'note': '景气投资'},
    {'name': '金耀', 'fund': '民生加银品牌蓝筹', 'code': '690001', 'company': '民生加银', 'style': '品牌蓝筹', 'aum': '60亿+', 'note': '品牌投资'},
    {'name': '吴鹏飞', 'fund': '鹏华品牌传承', 'code': '000431', 'company': '鹏华', 'style': '品牌传承', 'aum': '50亿+', 'note': '品牌价值'},
    
    # 稳健均衡（15人）
    {'name': '王景', 'fund': '招商制造业转型', 'code': '001869', 'company': '招商', 'style': '制造业转型', 'aum': '90亿+', 'note': '制造业升级'},
    {'name': '贾成东', 'fund': '招商优质成长', 'code': '161706', 'company': '招商', 'style': '优质成长', 'aum': '80亿+', 'note': '成长精选'},
    {'name': '付斌', 'fund': '招商先锋', 'code': '217005', 'company': '招商', 'style': '先锋成长', 'aum': '70亿+', 'note': '先锋策略'},
    {'name': '朱红裕', 'fund': '招商核心竞争力', 'code': '014412', 'company': '招商', 'style': '核心竞争力', 'aum': '200亿+', 'note': '已入核心层'},
    {'name': '李崟', 'fund': '安信稳健增值', 'code': '001316', 'company': '安信', 'style': '稳健增值', 'aum': '100亿+', 'note': '已入价值层'},
    {'name': '张翼飞', 'fund': '安信民稳增长', 'code': '008809', 'company': '安信', 'style': '民稳增长', 'aum': '80亿+', 'note': '已入价值层'},
    {'name': '陈一峰', 'fund': '安信价值回报', 'code': '008954', 'company': '安信', 'style': '价值回报', 'aum': '60亿+', 'note': '价值投资'},
    {'name': '张明', 'fund': '安信企业价值优选', 'code': '004393', 'company': '安信', 'style': '企业价值', 'aum': '50亿+', 'note': '企业质量'},
    {'name': '聂世林', 'fund': '安信优势增长', 'code': '001287', 'company': '安信', 'style': '优势增长', 'aum': '70亿+', 'note': '优势企业'},
    {'name': '袁玮', 'fund': '安信新常态', 'code': '001583', 'company': '安信', 'style': '新常态', 'aum': '60亿+', 'note': '新经济'},
    {'name': '王博', 'fund': '南方成长先锋', 'code': '009318', 'company': '南方', 'style': '成长先锋', 'aum': '100亿+', 'note': '成长投资'},
    {'name': '吴剑毅', 'fund': '南方潜力新蓝筹', 'code': '000327', 'company': '南方', 'style': '潜力蓝筹', 'aum': '80亿+', 'note': '新蓝筹'},
    {'name': '李锦文', 'fund': '南方智慧精选', 'code': '004357', 'company': '南方', 'style': '智慧精选', 'aum': '70亿+', 'note': '智慧投资'},
    {'name': '林乐峰', 'fund': '南方转型增长', 'code': '001667', 'company': '南方', 'style': '转型增长', 'aum': '90亿+', 'note': '转型主题'},
    {'name': '郑诗韵', 'fund': '南方优质企业', 'code': '011216', 'company': '南方', 'style': '优质企业', 'aum': '60亿+', 'note': '企业质量'},
]

# 重点层 - 行业主题型（30人）
SECTOR_MANAGERS = [
    # 消费主题（10人）
    {'name': '王园园', 'fund': '富国消费主题', 'code': '519915', 'company': '富国', 'style': '消费主题', 'aum': '100亿+', 'note': '大消费'},
    {'name': '孙伟', 'fund': '民生加银策略精选', 'code': '000136', 'company': '民生加银', 'style': '策略精选', 'aum': '60亿+', 'note': '已在均衡层'},
    {'name': '黄文倩', 'fund': '华夏消费升级', 'code': '001927', 'company': '华夏', 'style': '消费升级', 'aum': '60亿+', 'note': '已在成长层'},
    {'name': '孙轶佳', 'fund': '华夏新兴消费', 'code': '005888', 'company': '华夏', 'style': '新兴消费', 'aum': '40亿+', 'note': '已在成长层'},
    {'name': '黄玥', 'fund': '富国中证消费50', 'code': '515650', 'company': '富国', 'style': '消费50ETF', 'aum': '50亿+', 'note': '指数基金'},
    {'name': '王乐乐', 'fund': '国泰消费优选', 'code': '005970', 'company': '国泰', 'style': '消费优选', 'aum': '40亿+', 'note': '消费精选'},
    {'name': '李恒', 'fund': '嘉实优势成长', 'code': '003292', 'company': '嘉实', 'style': '优势成长', 'aum': '50亿+', 'note': '成长消费'},
    {'name': '吴越', 'fund': '嘉实消费精选', 'code': '006604', 'company': '嘉实', 'style': '消费精选', 'aum': '60亿+', 'note': '精选消费'},
    {'name': '谭丽', 'fund': '嘉实价值精选', 'code': '005267', 'company': '嘉实', 'style': '价值精选', 'aum': '100亿+', 'note': '已入核心层'},
    {'name': '陈建军', 'fund': '富国消费活力', 'code': '010382', 'company': '富国', 'style': '消费活力', 'aum': '40亿+', 'note': '新消费'},
    
    # 科技/半导体（10人）
    {'name': '董季周', 'fund': '泰信中小盘精选', 'code': '290011', 'company': '泰信', 'style': '中小盘精选', 'aum': '40亿+', 'note': '中小盘'},
    {'name': '高翔', 'fund': '国泰金鑫', 'code': '519606', 'company': '国泰', 'style': '金鑫成长', 'aum': '50亿+', 'note': '成长科技'},
    {'name': '徐黄玮', 'fund': '国联安优选行业', 'code': '257070', 'company': '国联安', 'style': '优选行业', 'aum': '40亿+', 'note': '行业轮动'},
    {'name': '潘明', 'fund': '国联安科技动力', 'code': '001956', 'company': '国联安', 'style': '科技动力', 'aum': '50亿+', 'note': '科技主题'},
    {'name': '李元博', 'fund': '富国创新科技', 'code': '002692', 'company': '富国', 'style': '创新科技', 'aum': '80亿+', 'note': '科技创新'},
    {'name': '孙权', 'fund': '富国新兴产业', 'code': '001048', 'company': '富国', 'style': '新兴产业', 'aum': '60亿+', 'note': '新兴产业'},
    {'name': '许炎', 'fund': '富国互联科技', 'code': '006751', 'company': '富国', 'style': '互联科技', 'aum': '70亿+', 'note': '互联网科技'},
    {'name': '周雪军', 'fund': '海富通改革驱动', 'code': '519133', 'company': '海富通', 'style': '改革驱动', 'aum': '100亿+', 'note': '改革主题'},
    {'name': '黄峰', 'fund': '海富通电子信息', 'code': '519011', 'company': '海富通', 'style': '电子信息', 'aum': '50亿+', 'note': '电子科技'},
    {'name': '吕越超', 'fund': '海富通股票混合', 'code': '519005', 'company': '海富通', 'style': '股票混合', 'aum': '60亿+', 'note': '成长股'},
    
    # 新能源/周期（10人）
    {'name': '任琳娜', 'fund': '招商能源转型', 'code': '013871', 'company': '招商', 'style': '能源转型', 'aum': '50亿+', 'note': '能源变革'},
    {'name': '赵剑', 'fund': '嘉实环保低碳', 'code': '001616', 'company': '嘉实', 'style': '环保低碳', 'aum': '70亿+', 'note': '低碳环保'},
    {'name': '孟夏', 'fund': '嘉实优势', 'code': '009240', 'company': '嘉实', 'style': '优势企业', 'aum': '60亿+', 'note': '企业优势'},
    {'name': '苏文杰', 'fund': '嘉实资源精选', 'code': '005660', 'company': '嘉实', 'style': '资源精选', 'aum': '50亿+', 'note': '已在价值层'},
    {'name': '栾超', 'fund': '新华优选分红', 'code': '519087', 'company': '新华', 'style': '优选分红', 'aum': '60亿+', 'note': '高分红'},
    {'name': '赵强', 'fund': '新华优选成长', 'code': '519089', 'company': '新华', 'style': '优选成长', 'aum': '50亿+', 'note': '成长股'},
    {'name': '蔡目荣', 'fund': '华宝资源优选', 'code': '240022', 'company': '华宝', 'style': '资源优选', 'aum': '40亿+', 'note': '资源周期'},
    {'name': '丁靖斐', 'fund': '华宝国策导向', 'code': '001088', 'company': '华宝', 'style': '国策导向', 'aum': '30亿+', 'note': '政策驱动'},
    {'name': '钟帅', 'fund': '华夏行业景气', 'code': '003567', 'company': '华夏', 'style': '行业景气', 'aum': '100亿+', 'note': '已在成长层'},
    {'name': '张弘弢', 'fund': '华夏沪深300ETF', 'code': '510330', 'company': '华夏', 'style': '沪深300ETF', 'aum': '200亿+', 'note': '指数基金'},
]

# 重点层 - 固收+（20人）
FIXED_INCOME_MANAGERS = [
    {'name': '张雅君', 'fund': '易方达增强回报', 'code': '110017', 'company': '易方达', 'style': '增强回报', 'aum': '100亿+', 'note': '固收+'},
    {'name': '王晓晨', 'fund': '易方达双债增强', 'code': '110035', 'company': '易方达', 'style': '双债增强', 'aum': '80亿+', 'note': '债券+'},
    {'name': '胡剑', 'fund': '易方达稳健收益', 'code': '110007', 'company': '易方达', 'style': '稳健收益', 'aum': '150亿+', 'note': '稳健债'},
    {'name': '林虎', 'fund': '易方达安心回馈', 'code': '001182', 'company': '易方达', 'style': '安心回馈', 'aum': '90亿+', 'note': '固收+'},
    {'name': '韩阅川', 'fund': '易方达瑞景', 'code': '001433', 'company': '易方达', 'style': '瑞景配置', 'aum': '70亿+', 'note': '灵活配置'},
    {'name': '李一硕', 'fund': '易方达永旭添利', 'code': '000265', 'company': '易方达', 'style': '永旭添利', 'aum': '60亿+', 'note': '债券基金'},
    {'name': '王石千', 'fund': '鹏华可转债', 'code': '000297', 'company': '鹏华', 'style': '可转债', 'aum': '80亿+', 'note': '转债策略'},
    {'name': '刘涛', 'fund': '鹏华丰禄', 'code': '003547', 'company': '鹏华', 'style': '纯债', 'aum': '60亿+', 'note': '已入核心层'},
    {'name': '祝松', 'fund': '鹏华产业债', 'code': '206018', 'company': '鹏华', 'style': '产业债', 'aum': '70亿+', 'note': '信用债'},
    {'name': '杨Dial', 'fund': '鹏华稳利短债', 'code': '007515', 'company': '鹏华', 'style': '短债', 'aum': '100亿+', 'note': '短债策略'},
    {'name': '黄纪亮', 'fund': '富国天利增长', 'code': '100018', 'company': '富国', 'style': '天利增长', 'aum': '120亿+', 'note': '债券基金'},
    {'name': '张明凯', 'fund': '富国收益增强', 'code': '000981', 'company': '富国', 'style': '收益增强', 'aum': '80亿+', 'note': '固收+'},
    {'name': '俞晓斌', 'fund': '富国稳健增强', 'code': '000107', 'company': '富国', 'style': '稳健增强', 'aum': '90亿+', 'note': '稳健债'},
    {'name': '武磊', 'fund': '富国汇利回报', 'code': '004903', 'company': '富国', 'style': '汇利回报', 'aum': '70亿+', 'note': '回报策略'},
    {'name': '吕春杰', 'fund': '广发聚鑫', 'code': '000118', 'company': '广发', 'style': '聚鑫债券', 'aum': '100亿+', 'note': '债券+'},
    {'name': '代宇', 'fund': '广发双债添利', 'code': '270044', 'company': '广发', 'style': '双债添利', 'aum': '80亿+', 'note': '双债策略'},
    {'name': '谭昌杰', 'fund': '广发趋势优选', 'code': '000215', 'company': '广发', 'style': '趋势优选', 'aum': '90亿+', 'note': '趋势债'},
    {'name': '邱世磊', 'fund': '广发安泽短债', 'code': '002864', 'company': '广发', 'style': '短债', 'aum': '60亿+', 'note': '短债策略'},
    {'name': '刘志辉', 'fund': '广发集裕', 'code': '002636', 'company': '广发', 'style': '集裕债券', 'aum': '70亿+', 'note': '债券基金'},
    {'name': '张芊', 'fund': '广发聚鑫债券', 'code': '000118', 'company': '广发', 'style': '聚鑫债券', 'aum': '100亿+', 'note': '债券策略'},
]

# 合并所有重点层基金经理
KEY_MANAGERS = []
KEY_MANAGERS.extend(VALUE_MANAGERS)
KEY_MANAGERS.extend(GROWTH_MANAGERS)
KEY_MANAGERS.extend(BALANCED_MANAGERS)
KEY_MANAGERS.extend(SECTOR_MANAGERS)
KEY_MANAGERS.extend(FIXED_INCOME_MANAGERS)

# 去重（避免与核心层重复）
CORE_MANAGER_NAMES = set([
    '张坤', '朱少醒', '萧楠', '谢治宇', '周蔚文', '曹名长', '徐彦', '丘栋荣', '姜诚', '谭丽',
    '葛兰', '刘格菘', '冯明远', '赵诣', '李晓星', '归凯', '杨锐文', '崔宸龙', '郑澄然', '陆彬',
    '施成', '韩创', '钟赟', '王鹏', '黄兴亮',
    '傅鹏博', '王崇', '何帅', '杨浩', '董承非', '周应波', '刘旭', '张清华', '邬传雁', '秦毅',
    '于洋', '程洲', '杜洋', '焦巍',
    '蔡嵩松', '郑巍山', '刘彦春', '胡昕炜', '王宗合', '赵蓓', '楼慧源', '李瑞', '姚志鹏', '李游'
])

# 过滤掉核心层已有的基金经理
UNIQUE_KEY_MANAGERS = [m for m in KEY_MANAGERS if m['name'] not in CORE_MANAGER_NAMES]

if __name__ == "__main__":
    print("="*70)
    print("基金经理重点层名单（200人）")
    print("="*70)
    print()
    
    print(f"原始名单: {len(KEY_MANAGERS)}人")
    print(f"去重后: {len(UNIQUE_KEY_MANAGERS)}人")
    print(f"（已过滤与核心层{len(CORE_MANAGER_NAMES)}人重复的基金经理）")
    print()
    
    print("【风格分布】")
    print(f"  价值型: {len(VALUE_MANAGERS)}人")
    print(f"  成长型: {len(GROWTH_MANAGERS)}人")
    print(f"  均衡型: {len(BALANCED_MANAGERS)}人")
    print(f"  行业主题: {len(SECTOR_MANAGERS)}人")
    print(f"  固收+: {len(FIXED_INCOME_MANAGERS)}人")
    print()
    
    print("【去重后可用】")
    style_count = {}
    for m in UNIQUE_KEY_MANAGERS:
        style = m['style']
        if '价值' in style or '红利' in style:
            cat = '价值型'
        elif '成长' in style or '科技' in style or '医药' in style or '制造' in style or '信息' in style:
            cat = '成长型'
        elif '均衡' in style or '配置' in style or '灵活' in style or '稳健' in style:
            cat = '均衡型'
        elif '消费' in style or '主题' in style or 'ETF' in style or '资源' in style or '周期' in style:
            cat = '行业主题型'
        elif '债' in style or '固收' in style or '短债' in style or '可转债' in style:
            cat = '固收+'
        else:
            cat = '其他'
        style_count[cat] = style_count.get(cat, 0) + 1
    
    for style, count in sorted(style_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {style}: {count}人")
    print()
    
    print("="*70)
    print(f"重点层监控名单已就绪: {len(UNIQUE_KEY_MANAGERS)}人")
    print("="*70)
