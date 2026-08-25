(function knitCompassExhibitionSupplierMasterV1(global) {
  "use strict";

  const spinexpoRows = [
    ["SESH26-001", "Ailiwei Cashmere", "艾力薇羊绒", "Standard Package Booth", true],
    ["SESH26-002", "Qinghe County Aoyu Cashmere Products Co. Ltd", "清河县奥羽绒毛制品有限公司", "Raw Space", true],
    ["SESH26-003", "Asia Nuance Apparel Co., Ltd", "苏州雅斯时装有限公司", "Raw Space", true],
    ["SESH26-004", "Baoding Aurumis Cashmere Co. Ltd", "保定鼎泰羊绒科技有限公司", "Raw Space", true],
    ["SESH26-005", "Jiangsu Axor Co. Ltd", "江苏阿克索贸易有限公司", "Standard Package Booth", true],
    ["SESH26-006", "Guangdong Baiyi Textile Technology Co. Ltd", "广东柏艺纺织科技有限公司", "Raw Space", true],
    ["SESH26-007", "Guangzhou Baoheng Textile Technology Co. Ltd", "广州宝恒纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-008", "Best Shan Co. Ltd", "贝石特山国际贸易（上海）有限公司", "Raw Space", true],
    ["SESH26-009", "Biella Yarn", "德国南毛集团横机纱线", "Raw Space", true],
    ["SESH26-010", "Hengshui Caizhiyuan Color Card Sales Co. Ltd", "衡水彩之源色卡定制有限公司", "Standard Package Booth", false],
    ["SESH26-011", "Zhejiang Carolina Textile Co. Ltd", "浙江卡罗莱纳纺织有限公司", "Standard Package Booth", true],
    ["SESH26-012", "Chamtex Limited", "卓越纺织有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-013", "Shanghai Chanmoo Textile Co. Ltd", "上海千墨纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-014", "Jiangyin Channel Textile Co. Ltd", "江阴海峡纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-015", "Tongxiang Chongfu Orient Weaving Co. Ltd", "桐乡市崇福东方针织股份有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-016", "Tongxiang City Chuangyi Textile Technology Co. Ltd", "桐乡市创易纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-017", "Wuxi Chunglong Textile Technology Co. Ltd", "无锡中隆纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-018", "Dongguan Chunzhiyun Digital Technology Co. Ltd", "东莞市春之韵数码科技有限公司", "Standard Package Booth", true],
    ["SESH26-019", "Competent Corporation Limited", "金栢成集团有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-020", "Consinee Group Co. Ltd", "康赛妮集团有限公司", "Raw Space", true],
    ["SESH26-021", "Shandong Dashing Cashmere Products Ltd", "山东德信羊绒科技股份有限公司", "Raw Space", true],
    ["SESH26-022", "Zhangjiagang Davis Textile Co. Ltd", "张家港戴维丝纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-023", "Chifeng Dongli Cashmere Ltd", "赤峰东黎羊绒股份有限公司", "Raw Space", true],
    ["SESH26-024", "Dongguan Donglin Spinning Technology Co. Ltd", "东莞市东霖纺纱科技有限公司", "Standard Package Booth", true],
    ["SESH26-025", "Zhejiang Dongqi Group", "浙江东企集团", "Raw Space", true],
    ["SESH26-026", "Jiangsu Dongzhihe New Fiber Technology Co. Ltd", "江苏东智禾新纤维科技有限公司", "Raw Space", true],
    ["SESH26-027", "Zhangjiagang Duoyou Yarn Manufacturing Co. Ltd", "张家港市多友纱线制造有限公司", "Standard Package Booth", true],
    ["SESH26-028", "Ningbo Dushu Wool Textile Co. Ltd", "宁波独树麻毛纺织有限公司", "Standard Package Booth", true],
    ["SESH26-029", "Jiangsu GTIG Eastar Co. Ltd", "江苏国泰亿达实业有限公司", "Raw Space", true],
    ["SESH26-030", "Changzhou Elite Textile Co. Ltd", "常州市武进爱利达纺织有限公司", "Standard Package Booth", true],
    ["SESH26-031", "Zhejiang Enze Textile Material Co. Ltd", "浙江恩泽纺织原料有限公司", "Standard Package Booth", true],
    ["SESH26-032", "Esen (Fancy)", "", "Raw Space", true],
    ["SESH26-033", "Jiangsu GTIG Esen Co. Ltd (Sustainable)", "江苏国泰亿盛实业有限公司", "Standard Package Booth", true],
    ["SESH26-034", "Jiangsu Excellent Textile Co. Ltd", "江苏联合利泰纺织有限公司", "Raw Space", true],
    ["SESH26-035", "Filpucci Spa & Filpiu (Zhangjiagang) Special Textile Products Co. Ltd", "菲利（张家港）特种纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-036", "Fortune Tech Co. Ltd", "", "Raw Space", true],
    ["SESH26-037", "Dongguan Fuguang Textile Co. Ltd", "东莞市福光纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-038", "Shanghai Galaxy Metallic Yarn Co. Ltd", "上海银之川金银线有限公司", "Standard Package Booth", true],
    ["SESH26-039", "Gears Apparel Sourcing Ltd", "", "Knitwear Pavilion Stands", false],
    ["SESH26-040", "Gotex Global Co. Ltd", "高泰環球有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-041", "Jiangsu Guotai Huasheng Industrial Co. Ltd (GTHS)", "江苏国泰华盛实业有限公司", "Raw Space", true],
    ["SESH26-042", "GTI S.p.A. (Grupo Tessile Industriale S.p.A.)", "德国南毛集团奢华纱", "Raw Space", true],
    ["SESH26-043", "Guideline", "界线GUIDELINE", "Raw Space", true],
    ["SESH26-044", "Jiangsu Haite Fashion Textile Co. Ltd", "江苏海特纺织服装有限公司", "Raw Space", true],
    ["SESH26-045", "Jiangsu Haoye Fiber Technology Co. Ltd", "江苏浩业纤维科技有限公司", "Standard Package Booth", true],
    ["SESH26-046", "Happy Yarn", "嘉兴海贝纱线", "Standard Package Booth", true],
    ["SESH26-047", "Hasegawa Corporation", "", "Standard Package Booth", true],
    ["SESH26-048", "Qinghe Heng'ao Velvet Products Co. Ltd", "清河县恒澳绒毛制品有限公司", "Standard Package Booth", true],
    ["SESH26-049", "Zhangjiagang City Hengjia Textile Co. Ltd", "张家港市恒佳纺织有限公司", "Standard Package Booth", true],
    ["SESH26-050", "Shandong Hengtai Textile Co. Ltd", "山东恒泰纺织有限公司", "Raw Space", true],
    ["SESH26-051", "Tongxiang Hesen Textile Co. Ltd", "桐乡市赫森纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-052", "Hong Kong Ascends International Clothing", "", "Knitwear Pavilion Stands", false],
    ["SESH26-053", "Suzhou Hongbo Textile Co. Ltd", "苏州鸿柏纺织有限公司", "Standard Package Booth", true],
    ["SESH26-054", "Inner Mongolia Hongtai Industry - Textile Road", "内蒙古宏泰实业 - 纺道", "Standard Package Booth", true],
    ["SESH26-055", "Hongye Cashmere Co. Ltd", "宏业羊绒有限公司", "Raw Space", true],
    ["SESH26-056", "Guangdong Hotsun Textile Co. Ltd", "广东晧信纺织有限公司", "Standard Package Booth", true],
    ["SESH26-057", "Tonxiang Huajiana Cashmere Garments Co. Ltd", "桐乡市华家那羊绒服饰有限公司", "Raw Space", true],
    ["SESH26-058", "Jiangyin Huayang Textile Co. Ltd", "江阴华阳毛纺有限公司", "Standard Package Booth", true],
    ["SESH26-059", "Dongguan Huayi Textile Co. Ltd", "东莞市华毅纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-060", "Jiaxing Huayi Co. Ltd", "嘉兴市华益股份有限公司", "Raw Space", true],
    ["SESH26-061", "Zhangjiagang Huayi Textile Co. Ltd", "张家港市华益纺织有限公司", "Standard Package Booth", true],
    ["SESH26-062", "GTIG HUBO Industrial Co. Ltd", "江苏国泰汉帛实业发展有限公司", "Raw Space", true],
    ["SESH26-063", "Shanghai Hui Ge Textile Co. Ltd", "上海辉歌纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-064", "Shanghai Hywell Fibre Industry Co. Ltd", "上海凯威纤维工业有限公司", "Standard Package Booth", true],
    ["SESH26-065", "ICCI - Ningbo Mild Luxury Textiles Technology Co. Ltd", "ICCI - 康泰莱（宁波）纺织科技有限公司", "Raw Space", true],
    ["SESH26-066", "Inchon Textile Co. Ltd", "张家港仁川纺织有限公司", "Standard Package Booth", true],
    ["SESH26-067", "Ingtex Textiles Limited", "桐乡市菲拉缇纺织有限公司", "Standard Package Booth", true],
    ["SESH26-068", "Zhejiang Iray Cashmere Products Co. Ltd", "浙江依瑞羊绒制品有限公司", "Raw Space", true],
    ["SESH26-069", "Shanghai I-Sheen Industry Development Co. Ltd", "上海伊线实业发展有限公司", "Standard Package Booth", true],
    ["SESH26-070", "Guangdong Jiajia Textile Co. Ltd", "广东嘉佳纺织有限公司", "Standard Package Booth", true],
    ["SESH26-071", "Dongguan Jialun Textile Co. Ltd", "东莞市佳纶纺织有限公司", "Standard Package Booth", true],
    ["SESH26-072", "Jiangsu Jianlu Worsted Co. Ltd", "江苏箭鹿毛纺股份有限公司", "Raw Space", true],
    ["SESH26-073", "Shanghai Jiapeng Textile Technology Co. Ltd", "上海佳芃纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-074", "Zhejiang Jiarun Textile Technology Co. Ltd", "浙江嘉润纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-075", "Dongguan City Jiaxin Textile Co. Ltd", "东莞市佳欣纺织有限公司", "Standard Package Booth", true],
    ["SESH26-076", "Zhejiang Jiayun New Materials Co. Ltd", "浙江嘉云新材料有限公司", "Standard Package Booth", true],
    ["SESH26-077", "Suzhou Jicheng Knitting Apparel Co. Ltd", "苏州吉成针织服饰有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-078", "Jinfu Textile Co. Ltd", "锦福纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-079", "Jiangsu Jinlong Technology Ltd", "江苏金龙科技股份有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-080", "Dongguan Jin'Ousheng Textile Co. Ltd", "东莞市金瓯盛纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-081", "Haining Jinyonghe Household Textile Co. Ltd", "海宁金永和家纺织造有限公司", "Standard Package Booth", true],
    ["SESH26-082", "Jiangsu Jiuzhou Textile Co. Ltd", "江苏九州纺织有限公司", "Raw Space", true],
    ["SESH26-083", "Dongguan Joint Development Textile Technology Co. Ltd", "同发展纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-084", "Wudi Judexin Textile Co. Ltd", "无棣聚德鑫纺织有限公司", "Standard Package Booth", true],
    ["SESH26-085", "Jiangyin Kaibang Special Yarn Co. Ltd", "江阴市凯邦特种纱线有限公司", "Standard Package Booth", true],
    ["SESH26-086", "Shanghai Kaisore Textile Trading Co. Ltd", "上海凯苏尔纺织贸易有限公司", "Standard Package Booth", true],
    ["SESH26-087", "Kaplanlar Tekstil Sanayi Ve Ticaret A.S.", "", "Standard Package Booth", true],
    ["SESH26-088", "Ningbo Keze Textile Co. Ltd", "宁波科泽纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-089", "Inner Mongolia KVSS Trade Co. Ltd", "内蒙古凯维丝商贸有限公司", "Raw Space", true],
    ["SESH26-090", "Zhejiang Lanbao Wool Textile Group Co. Ltd", "浙江兰宝毛纺集团有限公司", "Standard Package Booth", true],
    ["SESH26-091", "Shanghai Lianda Li Trading Co. Ltd", "上海联达利商贸有限公司", "Standard Package Booth", true],
    ["SESH26-092", "Shanghai Lianding Textile Co. Ltd", "上海廉鼎纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-093", "Jiangsu Lianhong Textiles Co. Ltd", "江苏联宏纺织有限公司", "Raw Space", true],
    ["SESH26-094", "Loyal Light Fancy Yarns", "江西嘉盛精密纺织有限公司", "Raw Space", true],
    ["SESH26-095", "M.Oro International Limited", "美纤国际有限公司", "Raw Space", true],
    ["SESH26-096", "Shanghai Magicknit Fashion Co. Ltd", "上海利长制衣有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-097", "Jiaxing Minghai Core Spun Yarn", "嘉兴铭海包芯纱", "Standard Package Booth", true],
    ["SESH26-098", "Namyang Woolen Textile Co. Ltd", "南洋毛紡", "Standard Package Booth", true],
    ["SESH26-099", "Haiyan Nanbei Lake Textile Co. Ltd", "海盐南北湖毛纺有限公司", "Standard Package Booth", true],
    ["SESH26-100", "Shanghai Nanli Industrial Co. Ltd", "上海南丽实业有限公司", "Standard Package Booth", true],
    ["SESH26-101", "Dongguan City New Bamboo Textile Co. Ltd", "东莞市新竹纺织有限公司", "Standard Package Booth", true],
    ["SESH26-102", "Jiangyin New Chengyu Textile Technology Co. Ltd", "江苏新诚誉纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-103", "Jiangsu New Dynasty Textile Co. Ltd", "江苏新朝纺织品有限公司", "Raw Space", true],
    ["SESH26-104", "Zhangjiagang Bonded Logistics Park Noblefibres Imp & Exp Co. Ltd", "张家港保税物流园区东爱进出口有限公司", "Standard Package Booth", true],
    ["SESH26-105", "NSSOURCE", "罗思索丝", "Standard Package Booth", true],
    ["SESH26-106", "Zhangjiagang Free Trade Zone Onetex Co. Ltd", "张家港保税区艺佰意纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-107", "Orient Hongda", "", "Raw Space", true],
    ["SESH26-108", "Dongguan Outeng Clothing Co. Ltd", "东莞市欧腾服装有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-109", "Dongguan Qicaifang Cashmere Products Co. Ltd", "东莞市七彩纺羊绒制品有限公司", "Standard Package Booth", true],
    ["SESH26-110", "Dongguan Qingxiang Textile Co. Ltd", "东莞市青祥纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-111", "Shanghai Qiyi Textile Co. Ltd", "上海祺熠纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-112", "Jiangsu Rawtex Technology Co. Ltd", "江苏贝锦斐成纺织科技有限公司", "Raw Space", true],
    ["SESH26-113", "Jiangsu Lugang Science & Technology Co. Ltd (REGAL)", "江苏鹿港科技有限公司", "Raw Space", true],
    ["SESH26-114", "Ningbo Rising Textile Co. Ltd", "宁波瑞升纺织有限公司", "Standard Package Booth", true],
    ["SESH26-115", "Nantong Rongfeng Fibre Technology Co. Ltd", "南通荣丰纤维科技有限公司", "Standard Package Booth", true],
    ["SESH26-116", "Rongrun", "融润羊绒", "Raw Space", true],
    ["SESH26-117", "Roytex (HK) Limited", "", "Knitwear Pavilion Stands", false],
    ["SESH26-118", "Wujiang Runsun Textile Co. Ltd", "吴江市润昌纺织有限公司", "Raw Space", true],
    ["SESH26-119", "Zhangjiagang Free Trade Zone S&A International Trade Co. Ltd", "艾莎国际", "Raw Space", true],
    ["SESH26-120", "Suzhou Sanyuan Color Industry Co. Ltd", "苏州三原色实业有限公司", "Standard Package Booth", false],
    ["SESH26-121", "Sapiens Textile Development Co. Ltd", "上海赛彬丝纺织品科技有限公司", "Raw Space", true],
    ["SESH26-122", "Changzhou Shaliang Textile Technology Co. Ltd", "常州纱靓纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-123", "Shanghai Shanwei Textile Co. Ltd", "上海杉伟纺织品有限公司", "Raw Space", true],
    ["SESH26-124", "Shanghai Shi-Kwan Textile Group Co. Ltd", "上海世光纺织科技有限公司", "Raw Space", true],
    ["SESH26-125", "Wuxi Shilead Spinning Science & Technology (Dyeing) Co. Ltd", "无锡夏利达纺织科技（漂染）有限公司", "Raw Space", true],
    ["SESH26-126", "Shanghai Show Tran Metallic Yarn Co. Ltd", "上海绣川金银线有限公司", "Standard Package Booth", true],
    ["SESH26-127", "Jiangyin Shuangtian Textile Co. Ltd", "江阴市双天纺织有限公司", "Hand Knitting Stands", true],
    ["SESH26-128", "Jiangsu Shuangyu Textile Co. Ltd", "江苏双余纺织有限公司", "Standard Package Booth", true],
    ["SESH26-129", "Wuxi Simian Textile Co. Ltd", "无锡四棉纺织有限公司", "Standard Package Booth", true],
    ["SESH26-130", "Jiangsu Soipoi Co. Ltd", "江苏苏源百宜贸易有限公司", "Raw Space", true],
    ["SESH26-131", "Shanghai SpinZ Technology Co. Ltd", "上海之纺科技有限公司", "Standard Package Booth", true],
    ["SESH26-132", "Spinzy Network Technology (Suzhou) Co. Ltd", "织合集网络科技（苏州）有限公司", "Standard Package Booth", false],
    ["SESH26-133", "Südwolle Group/Innovation Hub", "德国南毛集团 / 纱线智库", "Raw Space", true],
    ["SESH26-134", "Sullivans International (China) Co. Ltd", "南通苏利文贸易有限公司", "Hand Knitting Stands", true],
    ["SESH26-135", "Zhejiang Sunyouo Industrial Co. Ltd", "浙江尚源实业有限公司", "Standard Package Booth", true],
    ["SESH26-136", "Jiangsu Super Textile Technology Co. Ltd", "江苏乐艺锦纺织科技有限公司", "Raw Space", true],
    ["SESH26-137", "Tongxiang Tangola Speciality Fiber Co. Ltd", "桐乡唐古拉特种纤维有限公司", "Raw Space", true],
    ["SESH26-138", "Xinjiang Tianshan Wool Tex Stock Co. Ltd", "新疆天山毛纺织股份有限公司", "Standard Package Booth", true],
    ["SESH26-139", "Jiangsu Lugang Tianwei Science & Technology Co. Ltd", "江苏鹿港天纬科技有限公司", "Raw Space", true],
    ["SESH26-140", "Wuxi Tiger Industrial Co. Ltd", "无锡市虎牛制线厂", "Standard Package Booth", true],
    ["SESH26-141", "Todd & Duncan", "英国托德邓肯有限公司", "Raw Space", true],
    ["SESH26-142", "Shanghai Tongli Textiles Co. Ltd", "上海同力纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-143", "Shanghai Tongyu Textile Technology Co. Ltd", "上海桐渝纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-144", "Top Line (Ningbo) Textile Co. Ltd", "康宝莱（宁波）织造有限公司", "Raw Space", true],
    ["SESH26-145", "Trend Textile Technology Co. Ltd", "苏州欣源丰纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-146", "Shaanxi Tuocheng Cashmere Technology Co. Ltd", "陕西驼城绒业科技有限公司", "Raw Space", true],
    ["SESH26-147", "TX Yarn", "", "Standard Package Booth", true],
    ["SESH26-148", "United King Textile Ltd", "聯德紡織（香港）有限公司", "Standard Package Booth", true],
    ["SESH26-149", "Guilin Vertex Greentech Limited", "大行环创新科技控股有限公司", "Standard Package Booth", true],
    ["SESH26-150", "Zhejiang Wanxin Weishen Textile & Technology Co. Ltd", "浙江万新纬燊纺织科技有限公司", "Raw Space", true],
    ["SESH26-151", "Suzhou Weijie Textile Co. Ltd", "苏州维杰纺织有限公司", "Standard Package Booth", true],
    ["SESH26-152", "WFS Cashmere Industry Co. Ltd", "济南艺牧羊绒有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-153", "Winning Textile Co. Ltd", "", "Raw Space", true],
    ["SESH26-154", "Zhejiang Xianyang Industry Co. Ltd", "浙江鲜氧实业有限公司", "Standard Package Booth", true],
    ["SESH26-155", "Zhejiang Xianyue Textile Co. Ltd", "浙江纤月纺织品有限公司", "Raw Space", true],
    ["SESH26-156", "Dongguan Xifang Textile Technology Co. Ltd", "东莞市喜纺纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-157", "Ningxia Xinao Cashmere Co. Ltd", "宁夏新澳羊绒有限公司", "Raw Space", true],
    ["SESH26-158", "Zhejiang Xinao Textiles Inc", "浙江新澳纺织股份有限公司", "Raw Space", true],
    ["SESH26-159", "Jiangsu Xinfang Science & Technology Group Co. Ltd", "江苏新芳科技集团股份有限公司", "Raw Space", true],
    ["SESH26-160", "Tongxiang Xingguang Woolen Incorporated Company", "桐乡市星光毛纺有限公司", "Standard Package Booth", true],
    ["SESH26-161", "Chibi Xinglin Textile Co. Ltd", "赤壁市兴林纺织有限公司", "Standard Package Booth", true],
    ["SESH26-162", "Dongguan Xinhuang Textile Co. Ltd", "东莞市鑫皇纺织有限公司", "Standard Package Booth", true],
    ["SESH26-163", "Zhejiang Xinjinghe Textile Technology Co. Ltd", "浙江新景和纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-164", "Shanghai Xinnuo", "上海信诺", "Raw Space", true],
    ["SESH26-165", "Tongxiang City Xinxiang Textile Co. Ltd", "桐乡市鑫祥纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-166", "Hangzhou Yaoxin Textile Co. Ltd", "杭州耀欣纺织有限公司", "Standard Package Booth", true],
    ["SESH26-167", "Shanghai Yarn Resources Textile Co. Ltd", "上海织源纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-168", "Yarn Success Co. Ltd", "宁波市鄞州扬而丰纺织有限公司", "Standard Package Booth", true],
    ["SESH26-169", "Yarns & Colors Co. Ltd", "锦祥纺织科技（苏州）有限公司", "Raw Space", true],
    ["SESH26-170", "Dongguan Yidan Textile Co. Ltd", "东莞亿丹纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-171", "Zhejiang Yilei Woollen Spinning & Weaving Co. Ltd", "浙江依蕾毛纺织有限公司", "Raw Space", true],
    ["SESH26-172", "Zhejiang Yingshanhong Textile Science and Technology Co. Ltd", "浙江映山红纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-173", "Suzhou Yisibo Fashion Co. Ltd", "苏州奕思博时装有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-174", "Shanghai Yiwagoe Textile Co. Ltd", "上海依和越纺织品有限公司", "Standard Package Booth", true],
    ["SESH26-175", "Baoding Youshang Cashmere Textile Co. Ltd", "保定优尚羊绒制品有限公司", "Raw Space", true],
    ["SESH26-176", "Zhejiang Yuanrun Textile Science & Technology Co. Ltd", "浙江源润纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-177", "Nantong Yuanyuan Wool Spinning & Weaving Co. Ltd", "南通市圆缘毛纺织有限公司", "Standard Package Booth", true],
    ["SESH26-178", "Luyin Group Yucheng Cashmere Spinning Co. Ltd", "鲁银集团禹城羊绒纺织有限公司", "Standard Package Booth", true],
    ["SESH26-179", "Shanghai Yuexin Textile Technology Co. Ltd", "上海粤昕纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-180", "Suzhou Yunmato Clothes Co. Ltd", "苏州永玛特服装有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-181", "Wuxi Yusheng Yarn Co. Ltd", "无锡裕盛纱线有限公司", "Standard Package Booth", true],
    ["SESH26-182", "Rudong Zhengmao Garments Co. Ltd", "如东正茂服饰有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-183", "Jiangyin Zhenxin Woollen Textile Co. Ltd", "江阴市振新毛纺有限公司", "Standard Package Booth", true],
    ["SESH26-184", "Wuxi Zhiwu Garment Design Co. Ltd", "无锡知物服饰设计有限公司", "Knitwear Pavilion Stands", false],
    ["SESH26-185", "Zhejiang Zhiyan Creative Design Co. Ltd", "浙江织研创意设计有限公司", "Standard Package Booth", true],
    ["SESH26-186", "Zhejiang Zhongding Textile Co. Ltd", "浙江中鼎纺织股份有限公司", "Raw Space", true],
    ["SESH26-187", "Shanghai Zhongwo Textile Technology Co. Ltd", "上海中沃纺织科技有限公司", "Standard Package Booth", true],
    ["SESH26-188", "Ningbo Zhongxin Wool Textile Group Co. Ltd", "宁波中鑫毛纺集团有限公司", "Raw Space", true],
    ["SESH26-189", "Shanghai Zixin Textile Co. Ltd", "上海梓芯纺织有限公司", "Standard Package Booth", true]
  ];

  const yarnExpoRows = [
    ["YEA26-001", "Cotton Council International Shanghai Representative Office", "美国国际棉花协会上海代表处", "8.2", "Cotton Yarn", "棉纺", "China 中国", true],
    ["YEA26-002", "Ningbo Lefeng Supply Chain Co Ltd", "宁波乐丰供应链服务有限公司", "8.2", "Cotton Yarn", "棉纺", "China 中国", true],
    ["YEA26-003", "Qingdao Bangte Ecological Textile Technology Co Ltd", "青岛邦特生态纺织科技有限公司", "8.2", "Regenerated yarn", "再生纱", "China 中国", true],
    ["YEA26-004", "Shaoxing Guozhou Textile New Material Co Ltd", "绍兴国周纺织新材料有限公司", "8.2", "Cotton Yarn", "棉纺", "China 中国", true],
    ["YEA26-005", "Shangqiu (Nantong) Imp & Exp Co Ltd", "", "8.2", "Cotton Yarn", "棉纺", "China 中国", true],
    ["YEA26-006", "Toray Fibers (Nantong) Co Ltd", "", "8.2", "Synthetic Fibre", "合成纤维", "China 中国", true],
    ["YEA26-007", "Xiamen Naseem Trade Co Ltd", "厦门纳新贸易有限公司", "8.2", "Cotton Yarn", "棉纺", "China 中国", true],
    ["YEA26-008", "Ximkai Advanced Materials Manufacturing Co Ltd", "鑫凯高新材料制造有限公司", "8.2", "Fancy Yarn", "花式纱线", "China 中国", true],
    ["YEA26-009", "Zhangzhou Weiyi Chemical Fiber Co Ltd", "漳州伟伊化纤有限公司", "8.2", "Elastic yarns", "弹力纱线", "China 中国", true],
    ["YEA26-010", "Zhejiang Huzhou Weida Group Co Ltd", "浙江湖州威达集团股份有限公司", "8.2", "Cotton Yarn", "棉纺", "China 中国", true],
    ["YEA26-011", "Egyptian Co For Flax And Its Products", "", "8.2", "Flax/Ramie Fibre", "麻纤维", "Egypt 埃及", true],
    ["YEA26-012", "Sematex For Flax Products", "", "8.2", "Flax/Ramie Fibre", "麻纤维", "Egypt 埃及", true],
    ["YEA26-013", "Asun Paper Products Company Limited", "", "8.2", "Other", "其它", "Hong Kong China 中国香港", false],
    ["YEA26-014", "Better International Holding (HK) Limited", "邦特国际控股有限公司", "8.2", "Regenerated yarn", "再生纱", "Hong Kong China 中国香港", true],
    ["YEA26-015", "Bluelotus International Trade Limited", "蓝莲花国际贸易有限公司", "8.2", "Fancy Yarn", "花式纱线", "Hong Kong China 中国香港", true],
    ["YEA26-016", "Fast Tone International Limited", "", "8.2", "Wool Yarn", "毛纱", "Hong Kong China 中国香港", true],
    ["YEA26-017", "Keywin Trading Limited", "其运贸易有限公司", "8.2", "Cotton Yarn", "棉纺", "Hong Kong China 中国香港", true],
    ["YEA26-018", "Wai Hing HK Trading Co", "香港伟兴贸易公司", "8.2", "Elastic yarns", "弹力纱线", "Hong Kong China 中国香港", true],
    ["YEA26-019", "The Cotton Textiles Export Promotion Council", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-020", "Acme Yarns Private Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-021", "Amar International", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-022", "Avalon Cotyarn Impex LLP", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-023", "Cotseeds Corporation", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-024", "Elkins Tradelink", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-025", "Envision Exports Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-026", "Excel Enterprise", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-027", "Global Tex", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-028", "Gokul Yarns Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-029", "Indo Industries", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-030", "Kamal Cotspin Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-031", "Kanchan India Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-032", "Kewalram Textiles Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-033", "Kikani Exports", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-034", "Lahoti Overseas Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-035", "Le Merite", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-036", "Manjeet Cotton Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-037", "Manan Textech Global Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-038", "Niva Exports LLP", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-039", "Prime Yarns", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-040", "Raiyani Overseas", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-041", "Relishah Export", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-042", "RSB Cottex Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-043", "S.P.Yarns", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-044", "Salona Cotspin Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-045", "Shree Chintamani Knitting Pvt. Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-046", "Shreedhar Cotsyn Pvt. Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-047", "Shroff Textile Exports", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-048", "Spinfab Spinners", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-049", "Square Textile Ventures Pvt. Ltd.", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-050", "Technocraft Industries (India) Ltd.", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-051", "Texperts India Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-052", "Valson Polyester Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-053", "Commissionerate of Textiles Government of Tamil Nadu", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-054", "Pallava Textiles P Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-055", "Sambandan Spinning", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-056", "Shanmugappriya Textiles (P) Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-057", "Shree Hari Textiles", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-058", "Sivaraj Spinning Mills (P) Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-059", "Space Textiles Private Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-060", "Thiagarajar Mills Pvt Ltd", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-061", "VSM Weavess India Private Limited", "", "8.2", "Cotton Yarn", "棉纺", "India 印度", true],
    ["YEA26-062", "TVC Media and Promotion Pvt Ltd", "", "8.2", "Media", "媒体", "India 印度", false],
    ["YEA26-063", "Yajur Fibres Limited", "", "8.2", "Flax/Ramie Fibre", "麻纤维", "India 印度", true],
    ["YEA26-064", "Duniatex Group", "", "8.2", "Cotton Yarn", "棉纺", "Indonesia 印度尼西亚", true],
    ["YEA26-065", "PT DAN LIRIS", "", "8.2", "Cotton Yarn", "棉纺", "Indonesia 印度尼西亚", true],
    ["YEA26-066", "PT. Indo-Rama Synthetics Tbk", "", "8.2", "Cotton Yarn", "棉纺", "Indonesia 印度尼西亚", true],
    ["YEA26-067", "Toray Industries Inc", "", "8.2", "Synthetic Fibre", "合成纤维", "Japan 日本", true],
    ["YEA26-068", "Woolyarns Limited", "", "8.2", "Wool Yarn", "毛纱", "New Zealand 新西兰", true],
    ["YEA26-069", "Abtex International (Pvt) Ltd", "", "8.2", "Cotton Yarn", "棉纺", "Pakistan 巴基斯坦", true],
    ["YEA26-070", "Ihsan Cotton Products (Pvt) Ltd", "", "8.2", "Cotton Yarn", "棉纺", "Pakistan 巴基斯坦", true],
    ["YEA26-071", "NV Tex Sourcing", "", "8.2", "Cotton Yarn", "棉纺", "Pakistan 巴基斯坦", true],
    ["YEA26-072", "Xiamen Naseem Trade Co", "", "8.2", "Cotton Yarn", "棉纺", "Pakistan 巴基斯坦", true],
    ["YEA26-073", "Everest Textile Co Ltd", "宏远兴业股份有限公司", "8.2", "Synthetic Fibre", "合成纤维", "", true],
    ["YEA26-074", "Sun Yarn Textile Co Ltd", "三永纺织股份有限公司", "8.2", "Cotton Yarn", "棉纺", "", true],
    ["YEA26-075", "Tah Lee Textile Co Ltd", "大立纺织股份有限公司", "8.2", "Cotton Yarn", "棉纺", "", true],
    ["YEA26-076", "Tah Yao Textile Co Ltd", "大耀纺织股份有限公司", "8.2", "Cotton Yarn", "棉纺", "", true],
    ["YEA26-077", "Indorama Ventures Public Company Limited", "", "8.2", "", "", "Thailand 泰国", true],
    ["YEA26-078", "The Lurex Company Limited", "", "8.2", "Metalic yarns", "金银丝线", "United Kingdom 英国", true],
    ["YEA26-079", "Circ Inc", "", "8.2", "Regenerated yarn", "再生纱", "USA 美国", true],
    ["YEA26-080", "Cotton Council International", "美国国际棉花协会", "8.2", "Cotton Yarn", "棉纺", "USA 美国", true],
    ["YEA26-081", "Agency for the development of light industry under the cabinet of ministers of the Republic of Uzbekistan", "", "8.2", "Cotton Yarn", "棉纺", "Uzbekistan 乌兹别克斯坦", true],
    ["YEA26-082", "Hengbang Textile Vietnam Co Ltd", "", "8.2", "Cotton Yarn", "棉纺", "Vietnam 越南", true],
    ["YEA26-083", "Huamian (Vietnam) Textile Company Limited", "华棉(越南)纺织有限公司", "8.2", "Cotton Yarn", "棉纺", "Vietnam 越南", true],
    ["YEA26-084", "Importeer International Company Limited", "", "8.2", "Cotton Yarn", "棉纺", "Vietnam 越南", true],
    ["YEA26-085", "Market Union Group Company Limited", "", "8.2", "Cotton Yarn", "棉纺", "Vietnam 越南", true],
    ["YEA26-086", "Pho Tho Textile Company Ltd", "", "8.2", "Cotton Yarn", "棉纺", "Vietnam 越南", true],
    ["YEA26-087", "XDD Textile Company Limited", "", "8.2", "Cotton Yarn", "棉纺", "Vietnam 越南", true]
  ];

  function normalizedIdentity(value) {
    return String(value || "")
      .normalize("NFKC")
      .toLocaleLowerCase()
      .replace(/[^\p{Letter}\p{Number}]+/gu, "");
  }

  function identityKeys(nameEn, nameZh) {
    return [
      nameZh ? `zh:${normalizedIdentity(nameZh)}` : "",
      nameEn ? `en:${normalizedIdentity(nameEn)}` : ""
    ].filter(Boolean);
  }

  const supplierByIdentity = new Map();
  const suppliersById = new Map();

  function canonicalSupplierFor(participationId, nameEn, nameZh) {
    const keys = identityKeys(nameEn, nameZh);
    const matchedIds = [...new Set(keys.map((key) => supplierByIdentity.get(key)).filter(Boolean))];
    const matchedId = matchedIds.length === 1 ? matchedIds[0] : "";
    const supplierId = matchedId || participationId;
    if (!suppliersById.has(supplierId)) {
      suppliersById.set(supplierId, {
        id: supplierId,
        name_en: nameEn,
        name_zh: nameZh,
        display_name: nameZh ? `${nameEn} / ${nameZh}` : nameEn,
        search_text: `${nameEn} ${nameZh}`.trim(),
        aliases: new Set([nameEn, nameZh].filter(Boolean)),
        event_ids: new Set(),
        participation_ids: new Set()
      });
    } else {
      const supplier = suppliersById.get(supplierId);
      [nameEn, nameZh].filter(Boolean).forEach((value) => supplier.aliases.add(value));
      supplier.search_text = [...supplier.aliases].join(" ");
    }
    keys.forEach((key) => supplierByIdentity.set(key, supplierId));
    return suppliersById.get(supplierId);
  }

  function spinexpoCountry(nameEn) {
    if (["Hasegawa Corporation"].includes(nameEn)) return "Japan";
    if (["Biella Yarn", "Südwolle Group/Innovation Hub"].includes(nameEn)) return "Germany";
    if (["GTI S.p.A. (Grupo Tessile Industriale S.p.A.)"].includes(nameEn)) return "Italy";
    if (["Namyang Woolen Textile Co. Ltd"].includes(nameEn)) return "Korea";
    if (["Kaplanlar Tekstil Sanayi Ve Ticaret A.S."].includes(nameEn)) return "Turkey";
    if (["Todd & Duncan"].includes(nameEn)) return "United Kingdom";
    return "China";
  }

  function buildEvent(config, rows, rowMapper) {
    const exhibitors = rows.map((row) => {
      const mapped = rowMapper(row);
      const supplier = canonicalSupplierFor(mapped.id, mapped.name_en, mapped.name_zh);
      supplier.event_ids.add(config.id);
      supplier.participation_ids.add(mapped.id);
      return Object.freeze({
        ...mapped,
        supplier_master_id: supplier.id,
        display_name: mapped.name_zh ? `${mapped.name_en} / ${mapped.name_zh}` : mapped.name_en,
        search_text: `${mapped.name_en} ${mapped.name_zh}`.trim()
      });
    });
    return Object.freeze({
      ...config,
      aliases: Object.freeze(config.aliases),
      exhibitors: Object.freeze(exhibitors)
    });
  }

  const spinexpoEvent = buildEvent({
    id: "EVT-SPINEXPO-SH-2026-08",
    label: "2026年8月 SPIN EXPO（上海）",
    aliases: [
      "2026年8月SPIN EXPO",
      "2026年8月 SPIN EXPO",
      "SPIN EXPO 2026年8月",
      "SPINEXPO Shanghai August 2026"
    ],
    organizer_event_name: "SPINEXPO Shanghai — 47th Session",
    dates: "2026-08-25/2026-08-27",
    season: "2027年秋冬",
    venue: "Shanghai World Expo Exhibition and Convention Center",
    source_url: "https://spinexpo-sh.corpit.com.cn/EList/Elist.aspx",
    source_checked_at: "2026-07-31",
    source_status: "OFFICIAL_EXHIBITOR_LIST",
    exhibitor_scope: "ALL_EXHIBITORS_WITH_YARN_SUPPLIER_CANDIDATE_FLAG"
  }, spinexpoRows, ([id, nameEn, nameZh, boothType, supplierCandidate]) => ({
    id,
    name_en: nameEn,
    name_zh: nameZh,
    country_or_region: spinexpoCountry(nameEn),
    booth_type: boothType,
    supplier_candidate: supplierCandidate
  }));

  const yarnExpoEvent = buildEvent({
    id: "EVT-YARN-EXPO-AUTUMN-SH-2026-08",
    label: "2026年8月 Yarn Expo Autumn（上海）",
    aliases: [
      "2026年8月｜Yarn Expo Autumn 上海",
      "2026年8月 Yarn Expo",
      "Yarn Expo Autumn 2026",
      "Yarn Expo Autumn Shanghai 2026"
    ],
    organizer_event_name: "Yarn Expo Autumn 2026",
    dates: "2026-08-25/2026-08-27",
    venue: "National Exhibition and Convention Center (Shanghai)",
    source_url: "https://yarn-expo-autumn.hk.messefrankfurt.com/content/dam/messefrankfurt-redaktion/yarn_expo_autumn/downloads/yea26/YEA26_Exh_list_web_0724.pdf",
    source_page_url: "https://yarn-expo-autumn.hk.messefrankfurt.com/shanghai/zh-cn/exhibitor-search.html",
    source_checked_at: "2026-07-31",
    source_list_as_of: "2026-07-24",
    source_status: "OFFICIAL_PROVISIONAL_EXHIBITOR_LIST",
    exhibitor_scope: "ALL_EXHIBITORS_WITH_YARN_AND_FIBRE_CANDIDATE_FLAG"
  }, yarnExpoRows, ([id, nameEn, nameZh, hall, productGroupEn, productGroupZh, countryOrRegion, supplierCandidate]) => ({
    id,
    name_en: nameEn,
    name_zh: nameZh,
    country_or_region: countryOrRegion,
    hall,
    product_group_en: productGroupEn,
    product_group_zh: productGroupZh,
    supplier_candidate: supplierCandidate
  }));

  const events = Object.freeze([spinexpoEvent, yarnExpoEvent]);
  const suppliers = Object.freeze([...suppliersById.values()].map((supplier) => Object.freeze({
    ...supplier,
    aliases: Object.freeze([...supplier.aliases]),
    event_ids: Object.freeze([...supplier.event_ids]),
    participation_ids: Object.freeze([...supplier.participation_ids])
  })));
  const participations = Object.freeze(events.flatMap((event) =>
    event.exhibitors.map((exhibitor) => Object.freeze({
      id: exhibitor.id,
      event_id: event.id,
      supplier_master_id: exhibitor.supplier_master_id,
      supplier_candidate: exhibitor.supplier_candidate
    }))
  ));

  global.KC_EXHIBITION_SUPPLIER_MASTER_V1 = Object.freeze({
    schema_version: "1.1",
    master_name: "Knit Compass Exhibition Supplier Master",
    relationship_model: "EXHIBITION_TO_PARTICIPATION_TO_SUPPLIER",
    suppliers,
    participations,
    events
  });
})(window);
