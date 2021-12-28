#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 採点プログラム

import traceback
import sys
import json
import itertools


def to_list(org_data):  # 実際には辞書型で作成している
    q_list = dict()
    a_list = dict()

    for i, line in enumerate(org_data):
        if "QAID" in line:
            id = line["QAID"]
        else:
            id = -1
        if "QorA" not in line:
            pass
        elif line["QorA"] == "Q":
            if id in q_list:
                q_list[id].append(i)
            else:
                q_list[id] = [i]
        elif line["QorA"] == "A":
            if id in a_list:
                a_list[id].append(i)
            else:
                a_list[id] = [i]
    if 0 in q_list:
        del q_list[0]
    if 0 in a_list:
        del a_list[0]
    if -1 in q_list:
        del q_list[-1]
    if -1 in a_list:
        del a_list[-1]

    return q_list, a_list


def make_alignment(org_data):  # alignment への変換
    q_list, a_list = to_list(org_data)
    keys = sorted(list(set(q_list.keys()) & set(a_list.keys())))

    alignment = []
    for k in keys:
        if k > 0:
            alignment.extend(list(itertools.product(q_list[k], a_list[k])))
    return alignment


def f1(precision, recall):
    if recall == 0:
        return 0
    return 2 * precision * recall / (precision + recall)


def separate(org_data):
    separated = dict()
    for i, line in enumerate(org_data):
        if "QuestionerID" in line and line["QuestionerID"]:
            if line["QuestionerID"] in separated:
                separated[line["QuestionerID"]].append(line)
            else:
                separated[line["QuestionerID"]] = [line]
    return separated


def evaluate(gs_org, tg_org):

    gs_data = separate(gs_org)
    tg_data = separate(tg_org)

    # for macro average
    sum_precision = 0
    sum_recall = 0
    sum_f1 = 0
    n = len(gs_data.keys())

    for id in gs_data.keys():
        gs_algn = make_alignment(gs_data[id])
        tg_algn = make_alignment(tg_data[id])
        gs_algn = set(gs_algn)
        tg_algn = set(tg_algn)

        numerator = len(gs_algn & tg_algn)
        if len(tg_algn) != 0:
            precision = numerator / len(tg_algn)
            recall = numerator / len(gs_algn)
            f = f1(precision, recall)
        else:
            precision = 0
            recall = 0
            f = 0

        sum_precision += precision
        sum_recall += recall
        sum_f1 += f

    avg_precision = sum_precision / n
    avg_recall = sum_recall / n
    avg_f1 = sum_f1 / n

    return avg_f1, avg_precision, avg_recall


# main

def main():
    input_file = sys.argv[1]  # 評価対象
    gold_standard_file = "PoliInfo3_QAAlignment_v20211120-Gold.json"  # 正解データ

    with open(gold_standard_file, 'r', encoding="utf-8-sig") as fp:
        gs_org = json.load(fp)

    with open(input_file, 'r', encoding="utf-8-sig") as fp:
        tg_org = json.load(fp)

    # いずれも質問者ごとのマクロ平均のため，この precision と recall の調和平均と，このF1値は一致しない
    f1, prec, rec = evaluate(gs_org, tg_org)

    return json.dumps({
        'status': 'success',
        'scores': [f1, prec, rec],
    }, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    try:
        print(main())
    except Exception:
        print(json.dumps({'status': 'failed'}, ensure_ascii=False))
        traceback.print_exc()
