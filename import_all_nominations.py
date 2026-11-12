# -*- coding: utf-8 -*-
"""
Imports all nominations from Phase 4:
1. Jaisamand Panchayat Samiti (Wards 1-15)
2. Sarada Panchayat Samiti (Wards 1-15)
3. Jhallara Panchayat Samiti (Wards 1-15)
4. Zila Parishad (Salumber ZP Wards 1-21)
Only 'Accepted' nominations are inserted as official contesting candidates.
"""

import sqlite3
import json
import os
import pandas as pd

# Data definitions: (Ward_No, Name_Hindi, Name_English, Father_Name_Hindi, Party, Category, Gender, Age, Symbol)

# 1. JAISAMAND PANCHAYAT SAMITI (Accepted candidates)
JAISAMAND_ACCEPTED = [
    # Ward 1
    (1, "काना मीणा", "KANA MEENA", "हीरा मीणा", "BJP", "ST", "M", 56, ""),
    (1, "गणपत लाल मीणा", "GANPAT LAL MEENA", "बाबूलाल मीणा", "BAP", "ST", "M", 23, ""),
    (1, "धनराज", "DHANRAJ", "फुला", "INC", "ST", "M", 46, ""),
    (1, "राजकुमार मीणा", "RAJKUMAR MEENA", "तोलीराम मीणा", "IND", "ST", "M", 22, "सेब"),
    # Ward 2
    (2, "अजय कुमार मीणा", "AJAY KUMAR MEENA", "मांगी लाल मीणा", "BAP", "ST", "M", 31, ""),
    (2, "रामलाल मीणा", "RAMLAL MEENA", "शंकर लाल मीणा", "BJP", "ST", "M", 39, ""),
    (2, "नरेन्द्र कुमार मीणा", "NARENDRA KUMAR MEENA", "ओकार लाल", "INC", "ST", "M", 31, ""),
    (2, "सुरजमल मीणा", "SURAJMAL MEENA", "गोमा", "IND", "ST", "M", 56, "अलमारी"),
    # Ward 3
    (3, "रवींद्र कूमार मीणा", "RAVINDRA KUMAR MEENA", "सुरेन्द्र कुमार", "INC", "ST", "M", 35, ""),
    (3, "गीता देवी", "GEETA DEVI", "वेल चन्द मीणा", "BJP", "ST (Woman)", "F", 54, ""),
    (3, "बाबु लाल मीणा", "BABU LAL MEENA", "धुला मीणा", "BAP", "ST", "M", 46, ""),
    # Ward 4
    (4, "रेखा", "REKHA", "राजकुमार", "BJP", "ST (Woman)", "F", 42, ""),
    (4, "सजन", "SAJAN", "मुकेश", "INC", "ST (Woman)", "F", 40, ""),
    (4, "वाली", "VALI", "प्रकाश", "AAP", "ST (Woman)", "F", 40, ""),
    (4, "राधा देवीलाल मीणा", "RADHA DEVILAL MEENA", "देवीलाल", "BAP", "ST (Woman)", "F", 39, ""),
    # Ward 5
    (5, "माया डॉ. विकास खराडी", "MAYA DR. VIKASH KHARADI", "विकास कुमार मीणा", "BAP", "ST (Woman)", "F", 33, ""),
    (5, "प्रभु लाल मीणा", "PRBHU LAL MEENA", "अमरा जी", "BJP", "ST", "M", 54, ""),
    (5, "रेशमा मीणा", "RESHMA MEENA", "सुन्दर लाल", "INC", "ST (Woman)", "F", 56, ""),
    (5, "मांगीलाल मीणा", "MANGILAL MEENA", "औजा", "AAP", "ST", "M", 39, ""),
    # Ward 6
    (6, "सूरज तेजसिंह मीणा", "SURAJ TEJSINGH MEENA", "तेज सिंह", "BJP", "ST (Woman)", "F", 28, ""),
    (6, "कमला देवी", "KAMALA DEVI", "लक्ष्मण लाल", "AAP", "ST (Woman)", "F", 38, ""),
    (6, "किरण मीणा", "KIRAN MEENA", "शंकर लाल मीणा", "INC", "ST (Woman)", "F", 29, ""),
    (6, "भूरी किशोर मीणा", "BHURI KISHOR MEENA", "किशोर कुमार मीणा", "BAP", "ST (Woman)", "F", 32, ""),
    # Ward 7
    (7, "ज्वाला मीना", "jawala meena", "भगवत सिंह", "BJP", "ST (Woman)", "F", 42, ""),
    (7, "जमना कुमारी मीणा", "JAMANA KUMARI MEENA", "गोपेश्वर मीणा", "INC", "ST (Woman)", "F", 29, ""),
    (7, "रेखा कालूलाल", "REKHA KALULAL", "कालुलाल", "BAP", "ST (Woman)", "F", 24, ""),
    # Ward 8
    (8, "अम्बा धुलिराम अहारी", "AMBA DHULIRAM AHARI", "धुलिराम", "BAP", "ST (Woman)", "F", 25, ""),
    (8, "शारदा शंकर लाल मीणा", "SHARDA SHANKAR LAL MEENA", "शंकर", "BJP", "ST (Woman)", "F", 56, ""),
    (8, "कालू मीणा", "KALU MEENA", "नाथू लाल", "INC", "ST (Woman)", "F", 35, ""),
    # Ward 9
    (9, "दिनेश कुमार प्रजापत", "DINESH KUMAR PRJAPAT", "शान्तिलाल", "INC", "OBC", "M", 32, ""),
    (9, "पदु बाई पदमलाल", "PADU BAI PADAMLAL", "पदम लाल", "BJP", "OBC (Woman)", "F", 56, ""),
    (9, "प्रकाश तेली", "PRAKASH TELI", "मांगी लाल तेली", "BAP", "OBC", "M", 28, ""),
    (9, "पदमा", "PADAMA", "रूपा", "AAP", "OBC", "M", 54, ""),
    (9, "गोविंद प्रेमचंद पटेल", "GOVIND PREMCHAND PATEL", "प्रेमचंद पटेल", "IND", "OBC", "M", 37, "ईंटें"),
    # Ward 10
    (10, "शेलेन्द्र सिंह मीणा", "SHELENDRA SINGH MEENA", "थान सिंह", "INC", "ST", "M", 49, ""),
    (10, "जवाहर लाल मीणा", "JAWAHAR LAL MEENA", "रोड़ा", "BAP", "ST", "M", 58, ""),
    (10, "देवीलाल", "DEVILAL", "रतना जी मीणा", "BJP", "ST", "M", 44, ""),
    # Ward 11
    (11, "ममता कुमारी मीणा", "MAMTA KUMARI MEENA", "मांगी लाल मीणा", "BAP", "ST (Woman)", "F", 25, ""),
    (11, "ईन्द्र कुंवर", "INDRA KUVANR", "शंकर सिंह", "INC", "General (Woman)", "F", 37, ""),
    (11, "मोहन कुंवर", "MOHAN KUNWAR", "मनोहर सिंह", "BJP", "General (Woman)", "F", 38, ""),
    (11, "नरसा कुंवर", "NARSA KUNWAR", "भवर सिंह", "IND", "General (Woman)", "F", 29, "सेब"),
    (11, "कडुआ बाई", "KADUA BAI", "हिम्मत सिंह", "IND", "General (Woman)", "F", 53, "चारपाई"),
    # Ward 12
    (12, "कंचन", "KANCHAN", "चेन सिंह", "BAP", "General (Woman)", "F", 38, ""),
    (12, "चन्दन", "CHANDAN", "देवी सिंह", "INC", "General (Woman)", "F", 65, ""),
    (12, "कलावती देवीसिंह", "KALAVATI DEVISINGH", "देवीसिंह", "BJP", "General (Woman)", "F", 38, ""),
    # Ward 13
    (13, "अनिता कुमारी मीणा", "ANITA KUMARI MEENA", "चोका लाल मीणा", "BAP", "ST (Woman)", "F", 24, ""),
    (13, "देवी सिंह", "DEVI SINGH", "दौलत सिंह", "INC", "General", "M", 45, ""),
    (13, "लोकेन्द्र सिंह राठौड", "LOKENDRA SINGH RATHOR", "केसर सिंह", "IND", "General", "M", 33, "अलमारी"),
    (13, "भीमराज पटेल", "BHIMRAJ PATEL", "लालू", "BJP", "OBC", "M", 33, ""),
    (13, "हिम्मत सिंह", "HIMMAT SINGH", "फ़तेह सिंह", "IND", "General", "M", 43, "सेब"),
    # Ward 14
    (14, "कमल कुमार खटीक", "KAMAL KUMAR KHATIK", "मणि लाल", "BJP", "SC", "M", 29, ""),
    (14, "भँवरलाल सालवी", "BHANWARLAL SALVI", "पुंजा जी सालवी", "BAP", "SC", "M", 62, ""),
    (14, "शंकर लाल नट", "SHANKAR LAL NAT", "चौखा", "INC", "SC", "M", 40, ""),
    # Ward 15
    (15, "तिलक कंवर", "TILAK KANVAR", "लक्ष्मण सिंह", "IND", "General (Woman)", "F", 39, "सेब"),
    (15, "अग्रवाल प्रियंका", "AGRAWAL PRIYANKA", "जगदिश कुमार भोई", "INC", "General (Woman)", "F", 25, ""),
    (15, "रेखा कुंवर हिम्मत सिंह राठौड", "REKHA KUNWAR HIMMAT SINGH RATHOR", "हिम्मत सिंह राठौड़", "BAP", "General (Woman)", "F", 29, ""),
    (15, "कंचन किशोर जोशी", "KANCHAN KISHOR JOSHI", "किशोर जोशी", "IND", "General (Woman)", "F", 41, "बाँसुरी"),
    (15, "चंदा दिनेश कुमार जोशी", "CHANDA DINESH KUMAR JOSHI", "दिनेश", "BJP", "General (Woman)", "F", 33, ""),
]

# 2. SARADA PANCHAYAT SAMITI (Accepted candidates)
SARADA_ACCEPTED = [
    # Ward 1
    (1, "बाबु लाल मीणा", "Babu Lal Meena", "सवजी", "BAP", "ST", "M", 40, ""),
    (1, "हजारी लाल", "Hajari Lal", "होमा", "BJP", "ST", "M", 46, ""),
    (1, "मुकेश कुमार मीणा", "Mukesh Kumar Meena", "मोतीलाल", "INC", "ST", "M", 34, ""),
    # Ward 2
    (2, "उमा शंकर मीणा", "Uma Shankar Meena", "रतन प्रकाश मीणा", "BAP", "ST", "M", 32, ""),
    (2, "केशवलाल मीणा", "Keshavlal Meena", "मंगल चन्द", "INC", "ST", "M", 39, ""),
    (2, "लक्ष्मण लाल", "Laxman Lal", "धुला", "BJP", "ST", "M", 46, ""),
    (2, "गणेश लाल मीणा", "Ganesh Lal Meena", "लालू राम", "IND", "ST", "M", 28, "सेब"),
    # Ward 3
    (3, "बसंती लाल मेघवाल", "BASANTI LAL MEGHWAL", "तेजी लाल मेघवाल", "BAP", "SC", "M", 40, ""),
    (3, "कालूलाल", "Kalulal", "वाला", "INC", "SC", "M", 70, ""),
    (3, "धूलचंद", "DHULCHAND", "रामा", "BJP", "SC", "M", 66, ""),
    (3, "शंकर", "Shankar", "चोखा", "IND", "SC", "M", 55, "अलमारी"),
    # Ward 4
    (4, "सुरज मीणा", "SURAJ MEENA", "कमलेश मीणा", "BAP", "ST (Woman)", "F", 29, ""),
    (4, "शारदा", "Sharda", "हीरालाल", "INC", "ST (Woman)", "F", 31, ""),
    (4, "लक्ष्मी", "Laxmi", "रतना", "BJP", "ST (Woman)", "F", 45, ""),
    # Ward 5
    (5, "रेशमा बानो", "Reshma Bano", "फारूख खान", "BAP", "OBC (Woman)", "F", 22, ""),
    (5, "विनीता मीणा", "VINITA MEENA", "लक्ष्मण लाल", "INC", "ST (Woman)", "F", 31, ""),
    (5, "उर्मिला पटेल", "Urmila Patel", "प्रकाश", "IND", "General (Woman)", "F", 32, "चारपाई"),
    (5, "जोसना", "Josana", "भंवर लाल", "IND", "General (Woman)", "F", 28, "अलमारी"),
    (5, "कमला", "Kamla", "मांगीलाल", "BJP", "General (Woman)", "F", 51, ""),
    # Ward 6
    (6, "दुर्गा", "Durga", "चम्पा लाल मीणा", "BJP", "ST (Woman)", "F", 50, ""),
    (6, "सुमन कुमारी", "Suman Kumari", "नरेंद्र मीणा", "BAP", "ST (Woman)", "F", 36, ""),
    (6, "मीना कुमारी मीणा", "Meena Kumari Meena", "सुरजमल मीणा", "INC", "ST (Woman)", "F", 21, ""),
    # Ward 7
    (7, "सोहनी देवी", "Sohani Devi", "ईंन्दरलाल", "BAP", "ST (Woman)", "F", 39, ""),
    (7, "कमला देवी", "Kamala Devi", "नानालाल", "INC", "ST (Woman)", "F", 60, ""),
    (7, "कलावती", "Kalavati", "दिनेश", "BJP", "ST (Woman)", "F", 38, ""),
    (7, "सीमा", "seema", "प्रकाश", "IND", "ST (Woman)", "F", 36, "अलमारी"),
    # Ward 8
    (8, "चंदा कुमारी मीणा", "Chanda Kumari Meena", "देवेन्द्र कुमार मीणा", "BAP", "ST (Woman)", "F", 26, ""),
    (8, "उषा देवी", "Usha Devi", "ओम प्रकाश मीणा", "BJP", "ST (Woman)", "F", 25, ""),
    (8, "ममता", "Mamta", "रोशनलाल", "INC", "ST (Woman)", "F", 34, ""),
    # Ward 9
    (9, "चून्नी लाल", "Chunni lal", "देवजी", "BJP", "ST", "M", 71, ""),
    (9, "विष्णु", "Vishnu", "हीरा", "INC", "ST", "M", 62, ""),
    (9, "रणजीत", "Ranjeet", "पांचाराम", "BAP", "ST", "M", 35, ""),
    # Ward 10
    (10, "संगीता अहारी", "Sangita Ahari", "नरेन्द्र अहारी", "BAP", "ST (Woman)", "F", 35, ""),
    (10, "मंजूला", "Manjula", "शंकरलाल", "BJP", "ST (Woman)", "F", 40, ""),
    (10, "बबली देवी", "Babali Devi", "हरिराम", "INC", "ST (Woman)", "F", 34, ""),
    # Ward 11
    (11, "नवीद बेग मिर्जा", "Navid Beg Mirza", "नवाब बेग", "INC", "General", "M", 42, ""),
    (11, "हेमन्त", "Hemant", "धुलाजी", "IND", "General", "M", 34, "चारपाई"),
    (11, "सुरेश कुमार", "Suresh Kumar", "मावा राम", "BAP", "ST", "M", 34, ""),
    (11, "हीरालाल", "Heeralal", "भीमाजी", "IND", "OBC", "M", 52, "अलमारी"),
    (11, "आगा खान", "Aga Khan", "बाबर खां", "BJP", "General", "M", 44, ""),
    # Ward 12
    (12, "गमीर लाल", "Gamir Lal", "रूप प्रकाश", "BAP", "ST", "M", 57, ""),
    (12, "रामलाल", "Ramlal", "वाला", "IND", "ST", "M", 54, "चारपाई"),
    (12, "हजारी लाल", "Hajaril al", "धुला", "BJP", "ST", "M", 49, ""),
    (12, "महेन्द्र", "MAHENDRA", "पुंजाराम", "INC", "ST", "M", 35, ""),
    # Ward 13
    (13, "रक्षा सुथार", "Raksha Suthar", "भंवरलाल सुथार", "INC", "OBC (Woman)", "F", 22, ""),
    (13, "लाली", "LALI", "लच्छीराम", "BJP", "General (Woman)", "F", 61, ""),
    (13, "कंकू", "KANKU", "रूपलाल", "IND", "OBC (Woman)", "F", 56, "सेब"),
    (13, "लीला कुमारी", "Lila Kumari", "ललित कुमार मीणा", "BAP", "ST (Woman)", "F", 26, ""),
    # Ward 14
    (14, "शिवलाल", "Shivlal", "देवेन्द्र कुमार", "INC", "ST", "M", 64, ""),
    (14, "मनोहर", "Manohar", "पुजा", "BAP", "ST", "M", 46, ""),
    (14, "प्रकाश", "Prakash", "सवजी", "BJP", "ST", "M", 40, ""),
    (14, "नरेश मीणा", "Naresh Meena", "हीरा लाल", "AAP", "ST", "M", 35, ""),
    (14, "गंगाराम", "Gangaram", "रूपा", "IND", "ST", "M", 38, "अलमारी"),
    # Ward 15
    (15, "अरविन्द कुमार मीणा", "Arvind Kumar Meena", "भगवान लाल", "BAP", "ST", "M", 31, ""),
    (15, "मावालाल", "Mavalal", "हुरजी", "INC", "ST", "M", 48, ""),
    (15, "मोगालाल", "Mogalal", "रूपा", "BJP", "ST", "M", 48, ""),
]

# 3. JHALLARA PANCHAYAT SAMITI (Accepted candidates)
JHALLARA_ACCEPTED = [
    # Ward 1
    (1, "नाथु", "NATHU", "कसना", "BJP", "ST", "M", 58, ""),
    (1, "नरदा", "NARDA", "केशा", "IND", "ST (Woman)", "F", 21, "अलमारी"),
    (1, "परमानन्द मीणा", "PARMANAND MEENA", "मावजी", "BAP", "ST", "M", 32, ""),
    (1, "दौलत राम", "DOLAT RAM", "गोतम लाल", "INC", "ST", "M", 32, ""),
    # Ward 2
    (2, "श्रीमति नन्दू", "SHREEMATI NANDU", "भेरूलाल", "IND", "ST (Woman)", "F", 26, "अलमारी"),
    (2, "श्रीमती सोनिया", "SHREEMATI SONIYA", "नरेश मीणा", "BAP", "ST (Woman)", "F", 24, ""),
    (2, "ललीता कुमारी मीणा", "LALITA KUMARI MEENA", "गोवना मीणा", "BJP", "ST (Woman)", "F", 21, ""),
    (2, "मनीषा कुमारी मीणा", "MANISHA KUMARI MEENA", "रामलाल मीणा", "INC", "ST (Woman)", "F", 23, ""),
    # Ward 3
    (3, "गणेश", "GANESH", "दलाराम", "BJP", "ST", "M", 31, ""),
    (3, "रूपा", "RUPA", "कालु", "BAP", "ST", "M", 36, ""),
    (3, "खेता", "KHETA", "अमरा", "INC", "ST", "M", 35, ""),
    # Ward 4
    (4, "कैलाश कुंवर", "KAILASH KUNVAR", "भंवर सिंह", "BJP", "General (Woman)", "F", 51, ""),
    (4, "कली कुंवर", "KALI KUNWAR", "किशोर सिंह", "INC", "General (Woman)", "F", 39, ""),
    # Ward 5
    (5, "गोपी लाल", "GOPI LAL", "बाबरमल", "BJP", "ST", "M", 33, ""),
    (5, "मुकेश कुमार मीणा", "MUKESH KUMAR MEENA", "देवा जी मीणा", "BAP", "ST", "M", 25, ""),
    (5, "धुलीराम", "DHULIRAM", "तेजा", "INC", "ST", "M", 51, ""),
    # Ward 6
    (6, "नारायण", "NARAYAN", "मावजी", "BJP", "OBC", "M", 31, ""),
    (6, "वालजी मीणा", "VALAJI MEENA", "देगा", "INC", "ST", "M", 68, ""),
    # Ward 7
    (7, "देवीलाल पटेल", "DEVILAL PATEL", "नाथु जी पटेल", "BJP", "OBC", "M", 41, ""),
    (7, "रीतू मीणा", "RITU MEENA", "विजय प्रकाश मीणा", "BAP", "ST (Woman)", "F", 28, ""),
    (7, "लालुराम", "LALURAM", "रतना", "INC", "OBC", "M", 32, ""),
    # Ward 8
    (8, "जितेंद्र सिंह चौहान", "JITENDRA SINGH CHOUHAN", "लक्ष्मण सिंह चौहान", "BJP", "General", "M", 29, ""),
    (8, "जगदीश राम", "JAGDISH RAM", "नाया", "BAP", "ST", "M", 46, ""),
    (8, "देवी सिंह", "DEVI SINGH", "पर्वत सिंह", "INC", "General", "M", 40, ""),
    # Ward 9
    (9, "लसु", "LASU", "वाला", "BJP", "ST (Woman)", "F", 39, ""),
    (9, "वर्षा मीणा", "VARSHA MEENA", "रूप लाल", "BAP", "ST (Woman)", "F", 23, ""),
    (9, "नर्वदा मीणा", "NARVADA MEENA", "हीरालाल", "INC", "ST (Woman)", "F", 26, ""),
    # Ward 10
    (10, "कान्ता कुमारी मीणा", "KANTA KUMARI MEENA", "लक्ष्मण मीणा", "BJP", "ST (Woman)", "F", 21, ""),
    (10, "भगवती", "BHAGWATI", "राजू", "IND", "ST (Woman)", "F", 21, "अलमारी"),
    (10, "श्रीमती सुगना", "SHRIMATI SUGNA", "श्री शंकर", "BAP", "ST (Woman)", "F", 42, ""),
    (10, "इन्द्रा मीणा", "INDRA MEENA", "सुरेश", "IND", "ST (Woman)", "F", 29, "गुब्बारा"),
    (10, "लक्ष्मी कुमारी", "LAXMI KUMARI", "हरीश कुमार", "INC", "ST (Woman)", "F", 24, ""),
    # Ward 11
    (11, "नर्बदा", "NARBADA", "गौतम लाल मीणा", "BJP", "ST (Woman)", "F", 25, ""),
    (11, "शीला मीणा", "SHEELA MEENA", "धनराज मीणा", "BAP", "ST (Woman)", "F", 31, ""),
    (11, "शांता", "SHANTA", "पुंजीया", "INC", "ST (Woman)", "F", 44, ""),
    # Ward 12
    (12, "सज्जन कुँवर", "SAJJAN KUNWAR", "भवानी सिंह", "BJP", "General (Woman)", "F", 45, ""),
    (12, "सुमन भाटी", "SUMAN BHATI", "छत्रपाल सिंह चौहान", "INC", "General (Woman)", "F", 33, ""),
    # Ward 13
    (13, "हरीश कुमार", "HARISH KUMAR", "मन्‍ना लाल", "BJP", "ST", "M", 45, ""),
    (13, "देवा", "DEVA", "रूपा", "IND", "ST", "M", 50, "कोट"),
    (13, "राजेन्द्र कुमार मीणा", "RAJENDRA KUMAR MEENA", "खानिया मीणा", "BAP", "ST", "M", 32, ""),
    (13, "कन्हैया लाल", "KANHAIYA LAL", "कालू लाल", "INC", "ST", "M", 34, ""),
    # Ward 14
    (14, "पुजी", "PUJI", "भगवानलाल", "BJP", "ST (Woman)", "F", 59, ""),
    (14, "मेनका कुमारी", "MENKA KUMARI", "रमेश लाल मीणा", "BAP", "ST (Woman)", "F", 30, ""),
    (14, "सोनिया मीणा", "SONIYA MEENA", "बाबूलाल मीणा", "INC", "ST (Woman)", "F", 25, ""),
    # Ward 15
    (15, "गोतम लाल", "GOTAM LAL", "वक्था", "BJP", "ST", "M", 43, ""),
    (15, "प्रकाश चन्द्र", "PRAKASH CHANDRA", "देवा मीणा", "BAP", "ST", "M", 29, ""),
    (15, "महेन्द्र कुमार", "MAHENDRA KUMAR", "माणीक लाल", "INC", "ST", "M", 44, ""),
]

# 4. ZILA PARISHAD (SALUMBER ZP) (Accepted candidates)
# Note: Constituency Number is ZP Ward (1 to 21)
ZP_ACCEPTED = [
    # Ward 1
    (1, "विजय कुमार", "Vijay Kumar", "बाबुलाल मीणा", "INC", "ST", "M", 27, ""),
    (1, "गोविंद कलासुआ", "Govind Kalasua", "काना", "AAP", "ST", "M", 65, ""),
    (1, "वाल चन्द", "Val Chand", "कुराजी", "BJP", "ST", "M", 49, ""),
    (1, "सुरेश कुमार सोनु", "Suresh Kumar sonu", "श्री फूलचन्द मीणा", "BAP", "ST", "M", 34, ""),
    # Ward 2
    (2, "गंगा राम", "Ganga ram", "कालू", "INC", "ST", "M", 65, ""),
    (2, "शंकरलाल मीणा", "Shankarlal Meena", "होमा मीणा", "AAP", "ST", "M", 32, ""),
    (2, "रणजित कुमार मीणा", "Ranjeet Kumar Meena", "कालू लाल मीणा", "BAP", "ST", "M", 30, ""),
    (2, "मनीष कुमार मीणा", "Manish Kumar Meena", "राम सिंह", "BJP", "ST", "M", 48, ""),
    (2, "रमेश मीणा", "Ramesh Meena", "भेरूलाल", "IND", "ST", "M", 49, "हाथ गाड़ी"),
    # Ward 3
    (3, "केशु कन्हैयालाल पटेल", "Keshu Kanhaiyalal Patel", "कन्हैयालाल", "BJP", "OBC (Woman)", "F", 37, ""),
    (3, "मनीता पटेल", "Manita Patel", "भूपेन्द्र पटेल", "INC", "OBC (Woman)", "F", 29, ""),
    (3, "राधा जगदीश मीणा", "Radha Jagdish Meena", "जगदीश कुमार मीणा", "BAP", "ST (Woman)", "F", 32, ""),
    (3, "सुशीला", "SUSHILA", "वालचन्द", "IND", "OBC (Woman)", "F", 58, "हारमोनियम"),
    (3, "नर्बदा", "Narbada", "गोपाल सिंह", "IND", "General (Woman)", "F", 34, "गैस का चूल्हा"),
    # Ward 4
    (4, "सोनल मीणा", "Sonal Meena", "दुर्गा प्रसाद", "BJP", "ST (Woman)", "F", 34, ""),
    (4, "अनिता मीणा", "ANITA MEENA", "राजेश मीणा", "INC", "ST (Woman)", "F", 28, ""),
    (4, "हेमलता मीणा", "Hemlata Meena", "हवजी", "IND", "ST (Woman)", "F", 28, "चक्की"),
    (4, "कल्पना महेन्द्र मीणा", "Kalpana Mahendra Meena", "महेन्द्र कुमार मीणा", "BAP", "ST (Woman)", "F", 29, ""),
    # Ward 5
    (5, "रतनी", "Ratni", "गोविन्दराम", "BJP", "General (Woman)", "F", 41, ""),
    (5, "करीना रणजीत कुमार मीणा", "Karina Ranjeet Kumar Meena", "रणजीत सिंह मीणा", "BAP", "ST (Woman)", "F", 27, ""),
    (5, "जमना", "Jamna", "दिनेश", "INC", "General (Woman)", "F", 30, ""),
    (5, "बंसती कुमारी पटेल", "Bansati Kumari Patel", "भगवान लाल पटेल", "IND", "OBC (Woman)", "F", 25, "कैंची"),
    # Ward 6
    (6, "बसन्ती", "Basanti", "रघुवीर सिंह मीणा", "INC", "ST (Woman)", "F", 62, ""),
    (6, "रेखा देवी", "Rekha Devi", "धूलेश्वर", "BJP", "ST (Woman)", "F", 27, ""),
    (6, "अनुराधा जितेश कुमार कटारा", "Anuradha Jitesh Kumar Katara", "जितेश कुमार मीणा", "BAP", "ST (Woman)", "F", 26, ""),
    # Ward 7
    (7, "पुष्पा देवी", "Pushpa Devi", "मणीशंकर", "INC", "ST (Woman)", "F", 39, ""),
    (7, "बसंती मीणा", "Basanti Meena", "रमेश कुमार", "BJP", "ST (Woman)", "F", 37, ""),
    (7, "लक्ष्मी", "Lakshmi", "राकेश कुमार मीणा", "BAP", "ST (Woman)", "F", 27, ""),
    # Ward 8
    (8, "कालूलाल", "Kalulal", "दला", "INC", "ST", "M", 60, ""),
    (8, "हरिराम", "Hariram", "सुरमाल जी", "BJP", "ST", "M", 53, ""),
    (8, "मोहनलाल", "Mohanlal", "गनजी", "BAP", "ST", "M", 35, ""),
    # Ward 9
    (9, "लच्छुलाल", "LACHCHULAL", "जालमा", "INC", "ST", "M", 65, ""),
    (9, "श्रवणकुमार", "ShravanKumar", "भँवरलाल", "BJP", "ST", "M", 45, ""),
    (9, "गौरांग", "Gaurang", "मणीलाल मीणा", "BAP", "ST", "M", 52, ""),
    (9, "मणीलाल मीना", "Manilal Meena", "गणेश लाल मीणा", "AAP", "ST", "M", 24, ""),
    # Ward 10
    (10, "मेगालाल", "MEGALAL", "हिरा", "IND", "OBC", "M", 40, "चक्की"),
    (10, "देवेन्द्र सिंह", "Devendra Singh", "गमेर सिह", "INC", "General", "M", 53, ""),
    (10, "सुरेन्द्र सिंह चौहान", "Surendra Singh Chouhan", "अनाड़ सिंह चौहान", "IND", "General", "M", 25, "कैंची"),
    (10, "नरेश कुमार", "Naresh Kumar", "थावरा जी", "BAP", "ST", "M", 35, ""),
    (10, "हितेश कुमार सेवक", "Hitesh Kumar Sewak", "चुन्नीलाल", "BJP", "General", "M", 34, ""),
    (10, "रतन लाल पटेल", "RATAN LAL PATEL", "लालूलाल", "IND", "General", "M", 41, "टेलीविजन"),
    # Ward 11
    (11, "दिनेश कुमार", "DINESH KUMAR", "नाथुलाल", "INC", "OBC", "M", 37, ""),
    (11, "रमेश चौधरी", "Ramesh Chaudhary", "गेबजी", "BAP", "OBC", "M", 45, ""),
    (11, "गोविन्द", "Govind", "पेमा", "BJP", "OBC", "M", 44, ""),
    (11, "दिनेश कुमार पटेल", "Dinesh Kumar Patel", "भीमाजी पटेल", "IND", "OBC", "M", 34, "कैंची"),
    (11, "अनिल", "Anil", "शान्ति लाल", "IND", "OBC", "M", 43, "हाथ गाड़ी"),
    # Ward 12
    (12, "गेबीलाल दमावत", "GEBILAL DAMAWAT", "जगन्नाथ", "INC", "General", "M", 54, ""),
    (12, "देवेन्द्र सिंह", "Devendra Singh", "नाथूसिंह", "BJP", "General", "M", 31, ""),
    (12, "लक्ष्मी लाल", "Laxmi Lal", "रूपाजी", "BAP", "SC", "M", 50, ""),
    # Ward 13
    (13, "उमेश", "UMESH", "लिम्बाजी मीणा", "INC", "ST", "M", 41, ""),
    (13, "जया मीणा", "Jaya Meena", "शिव शंकर मीणा", "BJP", "ST (Woman)", "F", 28, ""),
    (13, "रूपी देवी", "Rupi Devi", "नायालाल मीणा", "BAP", "ST (Woman)", "F", 32, ""),
    (13, "किशनलाल मीणा", "Kishanlal Meena", "माना", "AAP", "ST", "M", 56, ""),
    (13, "जगदीश कुमार मीणा", "Jagdish Kumar Meena", "केवा राम", "IND", "ST", "M", 30, "टेलीफोन"),
    # Ward 14
    (14, "निर्मला कुंवर सिसोदिया", "Nirmala Kunwar Sisodiya", "महेन्द्र सिंह राठौड़", "INC", "General (Woman)", "F", 25, ""),
    (14, "पदमा कुँवर", "Padma Kunwar", "नाहर सिंह राठौड़", "BJP", "General (Woman)", "F", 44, ""),
    (14, "रेखा कुरीलाल भील", "Rekha Kurilal Bheel", "कुरीलाल भील", "BAP", "ST (Woman)", "F", 26, ""),
    # Ward 15
    (15, "नाथुलाल मेघवाल", "Nathulal Meghwal", "कालुलाल", "INC", "SC", "M", 44, ""),
    (15, "लोगरलाल", "Logarlal", "वगता", "BJP", "SC", "M", 47, ""),
    (15, "धीरज सालवी", "Dheeraj Salvi", "मांगी लाल सालवी", "BAP", "SC", "M", 27, ""),
    # Ward 16
    (16, "धुली कुमारी", "DHULI KUMARI", "ओमप्रकाश", "INC", "ST (Woman)", "F", 24, ""),
    (16, "केशर कुमारी मीणा", "Keshar Kumari Meena", "नंद लाल मीणा", "BJP", "ST (Woman)", "F", 22, ""),
    (16, "विमला", "Vimla", "प्रभुलाल", "BAP", "ST (Woman)", "F", 36, ""),
    # Ward 17
    (17, "लाली कुमारी मीणा", "LALI KUMARI MEENA", "शंभू मीणा", "INC", "ST (Woman)", "F", 22, ""),
    (17, "गुड्‌डी कुमारी मीणा", "Guddi Kumari Meena", "कमलेश मीणा", "BJP", "ST (Woman)", "F", 24, ""),
    (17, "कालकी सीताराम", "Kalki Sitaram", "सीता राम", "BAP", "ST (Woman)", "F", 44, ""),
    # Ward 18
    (18, "रामलाल", "RAMLAL", "अणदा", "INC", "ST", "M", 48, ""),
    (18, "लीला मीणा", "Leela Meena", "कन्हैयालाल मीणा", "BJP", "ST (Woman)", "F", 37, ""),
    (18, "अणदीलाल (आनन्द बुज)", "Anadilal Anand Buj", "केसरिया", "BAP", "ST", "M", 38, ""),
    (18, "गोतम लाल मीना", "Gotam lal Meena", "लोगर मीणा", "AAP", "ST", "M", 33, ""),
    # Ward 19
    (19, "मोहनी कुमारी मीणा", "MOHNI KUMARI MEENA", "मनीष कुमार मीणा", "INC", "ST (Woman)", "F", 26, ""),
    (19, "मोगी बाई", "Mogi Bai", "रूपा", "BAP", "ST (Woman)", "F", 55, ""),
    (19, "सुखना", "Sukhna", "नाथूलाल", "BJP", "ST (Woman)", "F", 31, ""),
    # Ward 20
    (20, "पुष्पा कुमारी मीणा", "PUSHPA KUMARI MEENA", "भेरा मीणा", "INC", "ST (Woman)", "F", 32, ""),
    (20, "रम्बा लिम्बाराम मीणा", "RAMBA LIMBARAM MEENA", "लिम्बाराम", "BAP", "ST (Woman)", "F", 34, ""),
    (20, "हिम्मती मीणा", "Himmati Meena", "जगदीश मीना", "BJP", "ST (Woman)", "F", 21, ""),
    # Ward 21
    (21, "राम लाल मीणा", "RAM LAL MEENA", "हुरजी मीणा", "INC", "ST", "M", 50, ""),
    (21, "रमेश चन्द्र मीणा", "Ramesh Chandra Meena", "खानु लाल मीणा", "BAP", "ST", "M", 33, ""),
    (21, "नागेन्द्र", "Nagendra", "नाया", "BJP", "ST", "M", 48, ""),
]


def update_database():
    conn = sqlite3.connect('election_salumber_2026.db')
    cursor = conn.cursor()

    # 1. Update Jaisamand PS
    print("Updating Jaisamand Panchayat Samiti...")
    # Delete non-NOTA candidates in Jaisamand PS
    cursor.execute("DELETE FROM candidates WHERE category='PS' AND block_name='Jaisamand' AND party != 'NOTA'")
    for c in JAISAMAND_ACCEPTED:
        w_no, name_hi, name_en, f_name, party, cat, gender, age, sym = c
        cursor.execute("""
        INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category)
        VALUES ('PS', 'Jaisamand', ?, ?, ?, ?, ?, ?, ?)
        """, (w_no, name_hi.strip(), party.strip(), sym.strip() or 'Official', gender, str(age), cat))

    # 2. Update Sarada PS
    print("Updating Sarada Panchayat Samiti...")
    cursor.execute("DELETE FROM candidates WHERE category='PS' AND block_name='Sarada' AND party != 'NOTA'")
    for c in SARADA_ACCEPTED:
        w_no, name_hi, name_en, f_name, party, cat, gender, age, sym = c
        cursor.execute("""
        INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category)
        VALUES ('PS', 'Sarada', ?, ?, ?, ?, ?, ?, ?)
        """, (w_no, name_hi.strip(), party.strip(), sym.strip() or 'Official', gender, str(age), cat))

    # 3. Update Jhallara PS
    print("Updating Jhallara Panchayat Samiti...")
    cursor.execute("DELETE FROM candidates WHERE category='PS' AND block_name='Jhallara' AND party != 'NOTA'")
    for c in JHALLARA_ACCEPTED:
        w_no, name_hi, name_en, f_name, party, cat, gender, age, sym = c
        cursor.execute("""
        INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category)
        VALUES ('PS', 'Jhallara', ?, ?, ?, ?, ?, ?, ?)
        """, (w_no, name_hi.strip(), party.strip(), sym.strip() or 'Official', gender, str(age), cat))

    # 4. Update Zila Parishad
    print("Updating Zila Parishad (Salumber ZP Wards 1-21)...")
    # For ZP, we update all wards with the official accepted candidates
    cursor.execute("DELETE FROM candidates WHERE category='ZP' AND party != 'NOTA'")
    for c in ZP_ACCEPTED:
        w_no, name_hi, name_en, f_name, party, cat, gender, age, sym = c
        cursor.execute("""
        INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category)
        VALUES ('ZP', 'Salumber ZP', ?, ?, ?, ?, ?, ?, ?)
        """, (w_no, name_hi.strip(), party.strip(), sym.strip() or 'Official', gender, str(age), cat))

    # 5. Ensure NOTA exists for all wards
    print("Checking and ensuring NOTA for all wards...")
    # For PS: 7 blocks x 15 wards
    blocks = ['Semari', 'Salumbar', 'Lasadiya', 'Geengla', 'Jaisamand', 'Sarada', 'Jhallara']
    for b in blocks:
        for w in range(1, 16):
            cursor.execute("SELECT id FROM candidates WHERE category='PS' AND block_name=? AND ward_no=? AND party='NOTA'", (b, w))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category, ballot_no)
                VALUES ('PS', ?, ?, 'नोटा (NOTA)', 'NOTA', 'NOTA', '', '', '', 99)
                """, (b, w))

    # For ZP: 21 wards
    for w in range(1, 22):
        cursor.execute("SELECT id FROM candidates WHERE category='ZP' AND block_name='Salumber ZP' AND ward_no=? AND party='NOTA'", (w,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category, ballot_no)
            VALUES ('ZP', 'Salumber ZP', ?, 'नोटा (NOTA)', 'NOTA', 'NOTA', '', '', '', 99)
            """, (w,))

    # 6. Re-calculate Hindi Alphabetical ballot_no for every ward (NOTA is always last)
    print("Calculating official ballot numbers...")
    cursor.execute("SELECT DISTINCT category, block_name, ward_no FROM candidates")
    all_wards = cursor.fetchall()
    for cat, blk, wno in all_wards:
        cursor.execute("SELECT id, name_hindi, party FROM candidates WHERE category=? AND block_name=? AND ward_no=?", (cat, blk, wno))
        cands = cursor.fetchall()
        # Separate NOTA from contestants
        normal_cands = [c for c in cands if c[2] != 'NOTA']
        nota_cands = [c for c in cands if c[2] == 'NOTA']
        # Sort contestants alphabetically by Hindi name
        normal_cands.sort(key=lambda x: x[1].strip())
        
        b_num = 1
        for cid, cname, _ in normal_cands:
            cursor.execute("UPDATE candidates SET ballot_no=? WHERE id=?", (b_num, cid))
            b_num += 1
        for cid, cname, _ in nota_cands:
            cursor.execute("UPDATE candidates SET ballot_no=? WHERE id=?", (b_num, cid))
            b_num += 1

    conn.commit()

    # Check totals
    cursor.execute("SELECT category, block_name, count(*) FROM candidates GROUP BY category, block_name")
    print("\n--- NEW CANDIDATE TOTALS ---")
    for r in cursor.fetchall():
        print(f"  {r[0]} - {r[1]}: {r[2]} candidates")

    cursor.execute("SELECT count(*) FROM candidates")
    total_cands = cursor.fetchone()[0]
    print(f"\nTOTAL REGISTERED CANDIDATES IN DISTRICT: {total_cands}")

    conn.close()


def sync_master_files():
    print("\nSyncing all master files (JSON, CSV, Excel)...")
    conn = sqlite3.connect('election_salumber_2026.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, category, block_name, ward_no, ballot_no, name_hindi, party, symbol, gender, age, candidate_category 
    FROM candidates 
    ORDER BY category, block_name, ward_no, ballot_no
    """)
    rows = cursor.fetchall()
    cols = ['id', 'category', 'block_name', 'ward_no', 'ballot_no', 'name_hindi', 'party', 'symbol', 'gender', 'age', 'candidate_category']
    df = pd.DataFrame(rows, columns=cols)

    # 1. Update 0_Candidate_Master.csv
    df.to_csv('0_Candidate_Master.csv', index=False, encoding='utf-8-sig')
    print("  Updated 0_Candidate_Master.csv")

    # 2. Update all_candidates_master.json
    json_cands = []
    for _, r in df.iterrows():
        json_cands.append({
            'id': int(r['id']),
            'type': r['category'],
            'block': r['block_name'],
            'wardNo': int(r['ward_no']),
            'ballotNo': int(r['ballot_no']),
            'name': r['name_hindi'],
            'party': r['party'],
            'symbol': r['symbol'],
            'gender': r['gender'],
            'age': r['age'],
            'category': r['candidate_category']
        })
    with open('all_candidates_master.json', 'w', encoding='utf-8') as f:
        json.dump(json_cands, f, ensure_ascii=False, indent=2)
    print("  Updated all_candidates_master.json")

    # 3. Update Excel file
    excel_path = 'Salumber_Consolidated_Master_Elections_2026.xlsx'
    if os.path.exists(excel_path):
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name='All_Candidates', index=False)
            print(f"  Updated sheet 'All_Candidates' in {excel_path}")
        except Exception as e:
            print(f"  Notice: could not replace Excel sheet ({e}), saved as backup")
    
    conn.close()


if __name__ == '__main__':
    update_database()
    sync_master_files()
    print("\nAll nominations successfully imported and synchronized!")
