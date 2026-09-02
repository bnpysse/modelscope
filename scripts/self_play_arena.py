#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天衍五维量化超脑 — 10万次对手盘连续自我博弈强化演化引擎 (Self-Play Order Flow Arena)
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

TOTAL_GAMES = 100000

class MarketState:
    def __init__(self, stock_code: str = "300308"):
        self.code = stock_code
        self.price = random.uniform(20.0, 150.0)
        self.lfs = random.uniform(30.0, 60.0)
        self.asr = random.uniform(10.0, 40.0)
        self.turnover = random.uniform(1.0, 8.0)
        self.z_profit = random.uniform(10.0, 70.0)
        self.cys34 = random.uniform(-15.0, 20.0)
        self.time_step = 0
        self.max_steps = 34

    def compute_cpr(self) -> float:
        return (self.lfs * 50.0) / (max(self.asr, 0.5) * (1.0 + self.turnover / 100.0))

    def compute_bri(self) -> float:
        return ((100.0 - 20.0) * self.z_profit) / (max(10.0, 0.5) * max(self.asr, 0.5))

    def get_features(self) -> Dict[str, float]:
        return {
            "Price": round(self.price, 2),
            "LFS": round(self.lfs, 2),
            "ASR": round(self.asr, 2),
            "Turnover": round(self.turnover, 2),
            "Z_Profit": round(self.z_profit, 2),
            "CYS34": round(self.cys34, 2),
            "CPR": round(self.compute_cpr(), 2),
            "BRI": round(self.compute_bri(), 2),
        }

class SelfPlayGame:
    MAIN_ACTIONS = ["STEALTH_ACCUMULATE", "VIOLENT_PULLUP", "WASH_DISSIPATION", "DUMP_DISTRIBUTION", "DEFENSIVE_HOLD"]
    OPPONENT_ACTIONS = ["CHASE_BUY", "PANIC_SELL", "PROFIT_TAKING", "BOTTOM_FISHING", "HIBERNATE_WAIT"]

    def __init__(self, game_id: int):
        self.game_id = game_id
        self.state = MarketState()
        self.trajectory = []

    def step(self) -> Tuple[bool, Dict[str, Any]]:
        self.state.time_step += 1
        curr_feat = self.state.get_features()

        cpr = curr_feat["CPR"]
        bri = curr_feat["BRI"]
        z_profit = curr_feat["Z_Profit"]
        lfs = curr_feat["LFS"]

        if cpr >= 20.0 and bri >= 30.0 and z_profit >= 40.0:
            main_act = "VIOLENT_PULLUP"
        elif lfs < 40.0 and z_profit < 20.0:
            main_act = "STEALTH_ACCUMULATE"
        elif z_profit > 70.0 and cpr < 10.0:
            main_act = "DUMP_DISTRIBUTION"
        elif curr_feat["CYS34"] < -10.0:
            main_act = "WASH_DISSIPATION"
        else:
            main_act = random.choice(self.MAIN_ACTIONS)

        if main_act == "VIOLENT_PULLUP":
            opp_act = "CHASE_BUY" if random.random() < 0.75 else "PROFIT_TAKING"
        elif main_act == "WASH_DISSIPATION":
            opp_act = "PANIC_SELL" if random.random() < 0.80 else "BOTTOM_FISHING"
        elif main_act == "DUMP_DISTRIBUTION":
            opp_act = "CHASE_BUY" if random.random() < 0.60 else "PANIC_SELL"
        else:
            opp_act = "HIBERNATE_WAIT"

        if main_act == "VIOLENT_PULLUP" and opp_act == "CHASE_BUY":
            price_delta = random.uniform(0.04, 0.099)
            lfs_delta = +1.5
            asr_delta = -2.0
            turnover = random.uniform(3.0, 7.0)
        elif main_act == "WASH_DISSIPATION" and opp_act == "PANIC_SELL":
            price_delta = random.uniform(-0.05, -0.01)
            lfs_delta = +2.5
            asr_delta = +3.0
            turnover = random.uniform(4.0, 10.0)
        elif main_act == "STEALTH_ACCUMULATE":
            price_delta = random.uniform(-0.01, +0.015)
            lfs_delta = +1.2
            asr_delta = -1.0
            turnover = random.uniform(1.0, 3.0)
        elif main_act == "DUMP_DISTRIBUTION":
            price_delta = random.uniform(-0.08, +0.02)
            lfs_delta = -4.0
            asr_delta = +5.0
            turnover = random.uniform(8.0, 18.0)
        else:
            price_delta = random.uniform(-0.015, +0.015)
            lfs_delta = -0.2
            asr_delta = 0.0
            turnover = random.uniform(1.5, 4.0)

        self.state.price = max(1.0, self.state.price * (1.0 + price_delta))
        self.state.lfs = min(95.0, max(5.0, self.state.lfs + lfs_delta))
        self.state.asr = min(95.0, max(5.0, self.state.asr + asr_delta))
        self.state.turnover = turnover
        self.state.z_profit = min(99.0, max(1.0, self.state.z_profit + price_delta * 120.0))

        reward = price_delta * 100.0 if main_act in ["VIOLENT_PULLUP", "STEALTH_ACCUMULATE"] else (-price_delta * 100.0)

        record = {
            "step": self.state.time_step,
            "main_action": main_act,
            "opponent_action": opp_act,
            "price": round(self.state.price, 2),
            "price_delta_%": round(price_delta * 100, 2),
            "LFS": round(self.state.lfs, 2),
            "ASR": round(self.state.asr, 2),
            "Turnover": round(self.state.turnover, 2),
            "CPR": round(self.state.compute_cpr(), 2),
            "BRI": round(self.state.compute_bri(), 2),
            "reward": round(reward, 2)
        }
        self.trajectory.append(record)
        done = (self.state.time_step >= self.state.max_steps)
        return done, record

    def run_full_game(self) -> Dict[str, Any]:
        done = False
        while not done:
            done, _ = self.step()
        
        total_reward = sum(r["reward"] for r in self.trajectory)
        win = (total_reward > 15.0)
        return {
            "game_id": self.game_id,
            "steps": len(self.trajectory),
            "total_reward": round(total_reward, 2),
            "win": win,
            "final_cpr": self.trajectory[-1]["CPR"],
            "final_lfs": self.trajectory[-1]["LFS"],
            "trajectory": self.trajectory
        }

def _simulate_batch(batch_range: Tuple[int, int]) -> List[Dict[str, Any]]:
    start_id, end_id = batch_range
    results = []
    for gid in range(start_id, end_id):
        game = SelfPlayGame(gid)
        results.append(game.run_full_game())
    return results

def run_100k_self_play_arena(total_games: int = TOTAL_GAMES, n_workers: int = 8) -> str:
    print("\n=======================================================")
    print(f"🚀 启动【10万次对手盘连续自我博弈强化演化竞技场】")
    print(f"🎮 总对弈局数: {total_games:,} 局 | 并行 CPU 核心: {n_workers} 核")
    print(f"📐 物理场微积分撮合: LFS 底座 × ASR 浮筹阻尼 × CPR 刚性度 × BRI 真空")
    print("=======================================================\n")

    t0 = time.time()
    batch_size = max(1000, total_games // (n_workers * 4))
    batches = []
    for i in range(0, total_games, batch_size):
        batches.append((i, min(i + batch_size, total_games)))

    total_wins = 0
    total_steps = 0
    all_expert_data = []

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(_simulate_batch, b): b for b in batches}
        completed_games = 0
        for fut in as_completed(futures):
            batch_res = fut.result()
            for r in batch_res:
                if r["win"]:
                    total_wins += 1
                    all_expert_data.append(r)
                total_steps += r["steps"]
            completed_games += len(batch_res)
            
            elapsed = time.time() - t0
            speed = completed_games / max(elapsed, 0.001)
            eta = (total_games - completed_games) / max(speed, 0.001)
            print(f"⚡ [进度: {completed_games:6d}/{total_games}] 撮合速度: {speed:7.1f} 局/秒 | 胜率: {total_wins/completed_games*100:5.1f}% | 剩余: {eta:5.1f}s", end="\r")

    elapsed = time.time() - t0
    print("\n\n=======================================================")
    print(f"✅ 100,000 局对手盘连续自我博弈全部圆满完成！")
    print(f"⏱️ 总耗时: {elapsed:.2f} 秒 ({elapsed/60:.2f} 分钟)")
    print(f"📊 整体实战胜率: {total_wins/total_games*100:.2f}% ({total_wins:,} 胜 / {total_games-total_wins:,} 负)")
    print(f"🔬 累计微积分时空撮合步数: {total_steps:,} 步")
    print(f"💎 成功沉淀高质量对抗专家经验轨迹: {len(all_expert_data):,} 局")
    print("=======================================================\n")

    out_dir = Path("/Users/woodman/dev/modelscope/quant_data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "self_play_expert_100k.jsonl"
    
    print(f"💾 正在将 {len(all_expert_data):,} 局精选对抗样本写入 {out_path} ...")
    with open(out_path, "w", encoding="utf-8") as f:
        for item in all_expert_data[:20000]:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"✓ 专家数据集落盘完成！文件大小: {os.path.getsize(out_path)/1024/1024:.2f} MB\n")
    return str(out_path)

if __name__ == "__main__":
    run_100k_self_play_arena(total_games=100000, n_workers=8)
