#!/usr/bin/env python3
"""
MicroSaaS MVP — Estrutura base para APIs monetizáveis.
Usa APENAS Python built-in (http.server + urllib + json + sqlite3).

Ideias de SaaS que este framework suporta:
- API de resumo de texto
- Gerador de QR codes
- Encurtador de URL
- API de transcrição/síntese
- API de tradução
- Bot de Telegram white-label
"""

import json
import sqlite3
import hashlib
import secrets
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── PRIVACY POLICY ────────────────────────────────────────
PRIVACY_POLICY_PATH = Path(__file__).parent / "privacy.html"

# ─── GUMROAD PRODUCT CATALOG ──────────────────────────────
PRODUCTS = [
    # ── Bundles ──
    {"slug": "bxssj", "name": "Life OS Mega Bundle -- 20 Digital Planners Complete System", "desc": "The ultimate life management system with 20 printable planners covering every area of your life: productivity, finance, health, habits, projects, and more. Everything you need to get organized in one bundle.", "price": 29.99, "category": "Bundle"},
    {"slug": "owwfcw", "name": "Productivity Pro -- 7 Planners Power Bundle", "desc": "Seven powerful planners to supercharge your productivity: weekly, daily, habit tracker, project manager, goal planner, time log, and priority matrix. Save 60% vs buying separately.", "price": 19.99, "category": "Bundle"},
    {"slug": "zgznvk", "name": "Starter Pack -- 5 Essential Digital Planners", "desc": "Get started with organization: Weekly Planner, Budget Tracker, Habit Tracker, Meal Planner, and Daily Journal — 5 essential planners at an unbeatable price.", "price": 14.99, "category": "Bundle"},

    # ── Planners ──
    {"slug": "uzbmvd", "name": "Ultimate Weekly Planner Printable — Hourly Schedule, Priority Tasks and Habit Tracker for Productivity (Undated A4/A5)", "desc": "Plan every week with purpose. Features hourly time blocking, priority task lists, habit tracker, weekly goals section, and reflection space. Undated — reuse year after year.", "price": 4.99, "category": "Planner"},
    {"slug": "cnnal", "name": "Student Budget Planner Printable — Monthly Income, Expense Tracker and Savings Goal for College Students", "desc": "Take control of your student finances. Track tuition, rent, groceries, and entertainment. Set savings goals and monitor your spending patterns month by month.", "price": 3.99, "category": "Planner"},
    {"slug": "uvinu", "name": "Teacher Gradebook Printable — Attendance, Grade Tracker and Assignment Log (Undated, Reusable)", "desc": "Stay on top of your classroom with this teacher-friendly gradebook. Track attendance, record grades, log assignments, and monitor student progress across multiple classes.", "price": 5.99, "category": "Planner"},
    {"slug": "yynktc", "name": "52-Week Savings Challenge Printable — $1,378 Money Tracker, Weekly Deposit Log and Financial Goal Planner (Undated PDF)", "desc": "Save $1,378 in one year with this proven weekly savings challenge. Track each deposit, watch your progress grow, and build a lasting savings habit.", "price": 3.99, "category": "Planner"},
    {"slug": "pbdqqi", "name": "Fitness Meal Prep Planner Printable — Weekly Menu, Macro Tracker and Grocery List for Gym and Weight Loss", "desc": "Transform your nutrition with weekly meal prep planning. Includes macro and calorie tracking, grocery lists, meal scheduling, and progress photos log.", "price": 4.99, "category": "Planner"},
    {"slug": "lkfju", "name": "Freelancer Finance Tracker Printable — Income, Expense and Tax Estimator Log for Independent Contractors (Undated, Reusable)", "desc": "Keep your freelance business finances organized. Track income by client, log deductible expenses, estimate quarterly taxes, and simplify tax season.", "price": 4.99, "category": "Planner"},

    # ── Health & Wellness ──
    {"slug": "hfwqoa", "name": "Health & Wellness Planner Printable — Monthly Fitness, Meal Prep and Self-Care Routine for Mind and Body", "desc": "A holistic wellness planner combining fitness tracking, meal planning, water intake logging, sleep tracking, and daily self-care routines. Undated and reusable.", "price": 4.99, "category": "Health"},
    {"slug": "mwdbkj", "name": "Symptom & Medication Tracker Printable — Chronic Illness Log, Pain Diary and Doctor Visit Planner", "desc": "Track daily symptoms, medications, pain levels, triggers, and treatments. Includes appointment prep pages and medication schedule. Essential for chronic illness management.", "price": 5.99, "category": "Health"},
    {"slug": "vjnxcr", "name": "Sleep & Mood Tracker Printable — 90-Day Log for Insomnia, Stress and Emotional Wellbeing", "desc": "Understand your sleep patterns and emotional wellbeing. Log bedtime, wake time, sleep quality, mood ratings, and daily stressors. Spot trends and improve your health.", "price": 3.99, "category": "Health"},
    {"slug": "tbfyqw", "name": "Water & Hydration Tracker Printable — 30-Day Daily Log with Goal Setting and Reminder Stickers", "desc": "Stay hydrated and feel better! Track daily water intake with easy-to-use log, set hydration goals, and use progress stickers to stay motivated.", "price": 2.99, "category": "Health"},
    {"slug": "rxcnak", "name": "Prenatal Health Journal Printable — Pregnancy Tracker, Appointment Log, Symptom Diary and Baby Prep Checklist", "desc": "Document your pregnancy journey week by week. Track symptoms, doctor appointments, fetal development notes, birth plan ideas, and nesting checklist.", "price": 5.99, "category": "Health"},

    # ── Baby & Parenting ──
    {"slug": "mlykrs", "name": "Baby Feeding & Diaper Log Printable — Newborn Tracker for Breastfeeding, Bottle, Sleep and Nappy Changes", "desc": "Essential tracker for new parents. Log breastfeeding sessions, bottle amounts, diaper changes, sleep times, and baby's mood. Perfect for pediatrician visits.", "price": 3.99, "category": "Baby"},
    {"slug": "wpqxzb", "name": "Baby Milestones & Memory Book Printable — First Year Journal with Monthly Updates, Photos and Keepsakes", "desc": "Capture every precious moment of baby's first year. Monthly milestone pages, photo pockets, firsts log, growth tracker, and letters to your baby.", "price": 6.99, "category": "Baby"},
    {"slug": "dsfnhy", "name": "Toddler Routine Chart Printable — Daily Schedule, Chore Chart and Reward System for Kids 2-5", "desc": "Establish healthy routines with your toddler. Visual daily schedule, morning/evening routine charts, chore trackers, and sticker reward system.", "price": 3.99, "category": "Baby"},
    {"slug": "kgbltm", "name": "Pregnancy Appointment & Birth Plan Planner Printable — Weekly Checklists, Lab Tracker and Hospital Bag Prep", "desc": "Stay organized throughout your pregnancy. Weekly checklists, appointment tracker, lab test log, birth plan worksheets, hospital bag checklist, and postpartum planning.", "price": 4.99, "category": "Baby"},

    # ── Productivity ──
    {"slug": "jptszh", "name": "Daily Time Blocking Planner Printable — Hourly Schedule from 6AM to 10PM (Undated, Letter/A4)", "desc": "Master your day with time blocking. Hourly schedule grid, top 3 priorities section, notes area, and evening reflection. Undated — start any day.", "price": 3.99, "category": "Productivity"},
    {"slug": "ngqvyu", "name": "Project Planner Printable — Task Tracker, Timeline Gantt and Milestone Log for Work and Side Projects", "desc": "Plan and execute projects with confidence. Task breakdown, Gantt timeline, milestone tracking, budget log, and weekly status pages. Perfect for freelancers and teams.", "price": 4.99, "category": "Productivity"},
    {"slug": "rcthmv", "name": "Goal Setting & Action Planner Printable — 90-Day Sprint, Quarterly OKRs and Weekly Progress Tracker", "desc": "Turn your goals into reality. Define quarterly OKRs, break them into 90-day sprints, track weekly progress, and review your achievements.", "price": 4.99, "category": "Productivity"},
    {"slug": "zqxkbf", "name": "Deep Work & Focus Tracker Printable — Pomodoro Sessions, Distraction Log and Daily Flow State Journal", "desc": "Optimize your focus and get more done. Track Pomodoro sessions, log distractions, rate your flow state, and analyze your most productive times of day.", "price": 3.99, "category": "Productivity"},

    # ── Finance & Organization ──
    {"slug": "vmpnry", "name": "Annual Budget Planner Printable — 12-Month Income & Expense Spreadsheet, Bill Tracker and Debt Payoff Log", "desc": "Your complete financial planning toolkit. 12-month budget spreadsheets, bill payment calendar, debt snowball tracker, savings goals, and net worth log.", "price": 5.99, "category": "Finance"},
    {"slug": "hkxfqw", "name": "Digital File Organizer Printable — Password Keeper, Software Licenses, Subscription Manager and Login Tracker", "desc": "Never lose track of your digital life. Log passwords (offline), track subscriptions, manage software licenses, and store important account details securely on paper.", "price": 3.99, "category": "Organization"},
    {"slug": "gpackf", "name": "Home Inventory & Cleaning Schedule Printable — Room-by-Room Organizer, Deep Cleaning Checklist and Maintenance Log", "desc": "Keep your home organized. Room-by-room inventory, deep cleaning schedules, maintenance reminders, seasonal task lists, and home improvement project tracker.", "price": 4.99, "category": "Organization"},
    {"slug": "xnvfkd", "name": "Bill Payment & Subscription Tracker Printable — Monthly Due Dates, Auto-Pay Log and Annual Renewal Calendar", "desc": "Never miss a payment again. Track all bills and subscriptions in one place, log due dates, check off payments, and plan for annual renewals.", "price": 2.99, "category": "Finance"},

    # ── Trackers ──
    {"slug": "bfprwg", "name": "Ultimate Habit Tracker Printable — 12-Month Daily Habit Log with Monthly Review and Habit Stacking Planner", "desc": "Build better habits with this comprehensive tracker. Track up to 12 habits daily for a full year, review monthly progress, and plan your habit stacking strategy.", "price": 4.99, "category": "Tracker"},
    {"slug": "emywbs", "name": "Travel Planner & Itinerary Organizer Printable — Trip Budget, Packing List, Journal and Souvenir Log", "desc": "Plan unforgettable trips. Itinerary pages, travel budget tracker, packing checklists, daily travel journal, photo log, and souvenir tracker.", "price": 4.99, "category": "Tracker"},
]

# ─── BLOG ARTICLES ────────────────────────────────────────
BLOG_ARTICLES = [
    {
        "slug": "best-digital-planners-2026",
        "title": "Best Digital Planners for 2026 — Ultimate Guide to Printable Planners",
        "meta_desc": "Discover the best digital planners for 2026. Compare weekly, monthly, and yearly printable planners to supercharge your productivity this year.",
        "h1": "Best Digital Planners for 2026",
        "content": """
<p>If you're looking to get organized in 2026, you've come to the right place. Digital planners — printable PDFs you can use on your tablet, iPad, or print at home — have exploded in popularity, and for good reason. They combine the flexibility of paper planning with the convenience of digital storage.</p>

<p>Whether you're a busy professional, a student juggling multiple deadlines, or a parent managing a household, the right planner can transform your productivity. In this guide, we'll walk through the best digital planners available for 2026 and help you choose the perfect one for your needs.</p>

<h2>Why Choose Digital Planners Over Paper?</h2>
<p>Digital planners offer several advantages over traditional paper planners. You can carry hundreds of pages on a single device, easily duplicate pages, and never run out of space. Many digital planners are undated, meaning you can start using them any time of year without wasting pages. Plus, they're eco-friendly — no trees required!</p>

<p>Printable planners also allow you to customize your planning system. Want a weekly spread with an hourly schedule? Done. Need a monthly budget tracker alongside your meal planner? Easy. The flexibility is unmatched.</p>

<h2>Top Digital Planners for 2026</h2>

<h3>1. Ultimate Weekly Planner — Hourly Schedule & Priority Tasks</h3>
<p>The <strong>Ultimate Weekly Planner</strong> is our top recommendation for anyone who wants to master their week. It features an hourly time-blocking schedule from 6 AM to 10 PM, priority task lists, a built-in habit tracker, and a weekly reflection section. It's undated, so you can start any week of the year.</p>
<p>Perfect for professionals who need to balance multiple projects, students managing coursework, or anyone who wants to make the most of their time.</p>
<p><a href="https://companymaster.gumroad.com/l/weekly-planner" target="_blank" rel="noopener">Get the Ultimate Weekly Planner →</a></p>

<h3>2. Productivity Pro Bundle — 7 Planners in One</h3>
<p>If you want a complete productivity system, the <strong>Productivity Pro Bundle</strong> is the way to go. It includes seven powerful planners: weekly, daily, habit tracker, project manager, goal planner, time log, and priority matrix. You save over 60% compared to buying each separately.</p>
<p>This bundle is ideal for power users who want every tool they might need in one download. From daily time blocking to long-term project planning, it's got you covered.</p>
<p><a href="https://companymaster.gumroad.com/l/productivity-bundle" target="_blank" rel="noopener">Get the Productivity Pro Bundle →</a></p>

<h3>3. Goal Setting & Action Planner — 90-Day Sprint System</h3>
<p>The <strong>Goal Setting Workbook</strong> helps you turn ambitious goals into actionable plans using a proven 90-day sprint system. Define quarterly OKRs, break them into weekly milestones, track progress, and review achievements. It's perfect for New Year's resolutions, career goals, or personal development.</p>
<p><a href="https://companymaster.gumroad.com/l/goal-setting" target="_blank" rel="noopener">Get the Goal Setting Workbook →</a></p>

<h2>How to Choose the Right Digital Planner</h2>
<p>Consider your planning style. Do you prefer hourly scheduling or a simpler task list? Do you need budget tracking alongside your calendar? Start with one planner that addresses your biggest pain point, then expand your system as you get comfortable.</p>

<p>For beginners, we recommend starting with the <strong>Ultimate Weekly Planner</strong> and adding the <strong>Habit Tracker</strong> once you've built a consistent planning routine.</p>

<h2>Final Thoughts</h2>
<p>2026 is the year to take control of your time. Digital planners make it easier than ever to stay organized, track your habits, and achieve your goals. Browse our full collection on <a href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Gumroad</a> and find the perfect planner for your needs.</p>
""",
        "products": [
            {"slug": "weekly-planner", "name": "Ultimate Weekly Planner"},
            {"slug": "productivity-bundle", "name": "Productivity Pro Bundle"},
            {"slug": "goal-setting", "name": "Goal Setting Workbook"}
        ]
    },
    {
        "slug": "how-to-organize-work-week",
        "title": "How to Organize Your Work Week — A Step-by-Step Guide to Weekly Planning",
        "meta_desc": "Learn how to organize your work week effectively with proven weekly planning strategies, time blocking techniques, and printable planners.",
        "h1": "How to Organize Your Work Week",
        "content": """
<p>Do you ever reach Friday and wonder where the week went? You're not alone. Most professionals struggle with weekly organization, bouncing between meetings, emails, and urgent tasks without a clear plan. The good news is that organizing your work week is a skill anyone can learn — and it starts with a solid weekly planning routine.</p>

<p>In this guide, we'll walk through a proven step-by-step system to organize your work week, reduce stress, and get more done.</p>

<h2>Why Weekly Planning Matters</h2>
<p>Weekly planning is the bridge between your big-picture goals and daily execution. Without a weekly plan, you're reacting to whatever comes your way. With one, you're proactively working on what matters most. Studies show that people who plan their week in advance are significantly more productive and report lower stress levels.</p>

<h2>Step 1: Review and Reflect (Sunday Evening or Monday Morning)</h2>
<p>Start your week by reviewing the previous week. What went well? What didn't get done? What priorities shifted? This 10-minute reflection helps you learn from the past and set intentional goals for the week ahead.</p>
<p>Use the <strong>Ultimate Weekly Planner</strong> to document your reflections and plan the coming days. Its built-in weekly reflection section makes this step effortless.</p>

<h2>Step 2: Identify Your Top 3 Priorities</h2>
<p>Before you schedule anything, identify the three most important outcomes for the week. These are the tasks that, if completed, will make the week a success. Everything else is secondary. Write them at the top of your weekly spread so they stay front and center.</p>

<h2>Step 3: Time Block Your Schedule</h2>
<p>Time blocking is the most effective way to protect your focus time. Divide your day into blocks dedicated to specific types of work: deep work, meetings, admin tasks, and breaks. Be realistic about how long things take and leave buffer time between blocks.</p>
<p>The <strong>Ultimate Weekly Planner</strong> includes an hourly schedule from 6 AM to 10 PM, perfect for time blocking your entire week.</p>

<h2>Step 4: Plan Your Meetings and Notes</h2>
<p>Meetings can be the biggest time-wasters if not managed well. For every meeting, set a clear agenda and take structured notes. After each meeting, document action items and decisions.</p>
<p>The <strong>Meeting Notes Template</strong> is designed specifically for this. It includes sections for agenda, discussion points, decisions, action items, and follow-up dates. Use it for every meeting and watch your meeting productivity soar.</p>
<p><a href="https://companymaster.gumroad.com/l/meeting-notes" target="_blank" rel="noopener">Get the Meeting Notes Template →</a></p>

<h2>Step 5: Track Your Habits</h2>
<p>Your weekly routine is built on habits. Whether it's daily exercise, reading, or focused work sessions, tracking your habits helps you stay consistent. Add 1-3 habits to track each week and review your progress on Friday.</p>
<p>The <strong>Habit Tracker</strong> is perfect for this — track up to 12 habits daily with monthly review pages to see your progress over time.</p>
<p><a href="https://companymaster.gumroad.com/l/habit-tracker" target="_blank" rel="noopener">Get the Habit Tracker →</a></p>

<h2>Step 6: End Each Day with a Review</h2>
<p>Spend 5 minutes at the end of each day reviewing what you accomplished, updating your task list, and setting tomorrow's priorities. This small habit prevents morning scramble and keeps you on track all week.</p>

<h2>Final Thoughts</h2>
<p>Organizing your work week doesn't have to be complicated. Start with these six steps, use the right tools, and you'll be amazed at how much more you can accomplish with less stress. Grab the <a href="https://companymaster.gumroad.com/l/weekly-planner" target="_blank" rel="noopener">Ultimate Weekly Planner</a> to put this system into action today.</p>
""",
        "products": [
            {"slug": "weekly-planner", "name": "Ultimate Weekly Planner"},
            {"slug": "meeting-notes", "name": "Meeting Notes Template"},
            {"slug": "habit-tracker", "name": "Habit Tracker"}
        ]
    },
    {
        "slug": "free-printable-habit-trackers",
        "title": "Free Printable Habit Trackers — Build Better Habits with These Proven Templates",
        "meta_desc": "Discover free printable habit tracker templates and learn how to build lasting habits. Includes links to premium habit tracking planners for serious habit builders.",
        "h1": "Free Printable Habit Trackers",
        "content": """
<p>Building good habits is the foundation of personal growth. Whether you want to exercise more, read daily, drink more water, or practice mindfulness, a habit tracker is one of the most effective tools to help you stay consistent. In this article, we'll explore how to use habit trackers effectively and share some of the best printable options available.</p>

<h2>Why Use a Habit Tracker?</h2>
<p>Habit tracking works because it harnesses several psychological principles. First, it creates a visual record of your progress — seeing a chain of checkmarks motivates you to keep going. Second, it reduces the mental effort of remembering whether you did a habit today. Third, it provides accountability to yourself.</p>
<p>Research shows that people who track their habits are significantly more likely to stick with them long-term. The simple act of checking a box creates a small dopamine reward that reinforces the behavior.</p>

<h2>Getting Started with Free Habit Trackers</h2>
<p>You can start tracking habits today with a simple notebook or a free printable template. Here's what a basic habit tracker should include:</p>
<ul>
<li>A list of habits you want to track (start with 3-5)</li>
<li>A grid with days of the month or week</li>
<li>Space to mark completion (checkmark, X, or color fill)</li>
<li>A monthly review section to analyze progress</li>
</ul>

<h2>Upgrade to the Ultimate Habit Tracker</h2>
<p>While free templates are great for getting started, the <strong>Habit Tracker</strong> from CompanyMaster takes your habit building to the next level. It includes:</p>
<ul>
<li>Track up to 12 habits daily for a full year</li>
<li>Monthly review pages with progress analysis</li>
<li>Habit stacking planner to build routines</li>
<li>Quarterly habit audits to refine your system</li>
<li>Beautiful, undated design — print as many copies as you need</li>
</ul>
<p><a href="https://companymaster.gumroad.com/l/habit-tracker" target="_blank" rel="noopener">Get the Ultimate Habit Tracker →</a></p>

<h2>Pair Goals with Habits</h2>
<p>Habits are the building blocks of goals. If you want to achieve something significant, break it down into daily habits and track them. The <strong>Goal Setting Workbook</strong> pairs perfectly with the Habit Tracker — use it to define your quarterly OKRs and track the daily habits that will get you there.</p>
<p><a href="https://companymaster.gumroad.com/l/goal-setting" target="_blank" rel="noopener">Get the Goal Setting Workbook →</a></p>

<h2>Popular Habit Categories to Track</h2>
<ul>
<li><strong>Health:</strong> Exercise, water intake, sleep, meditation, steps</li>
<li><strong>Productivity:</strong> Deep work hours, inbox zero, daily planning, reading</li>
<li><strong>Personal Growth:</strong> Journaling, learning, gratitude, skill practice</li>
<li><strong>Finance:</strong> Daily budget tracking, no-spend days, savings deposits</li>
</ul>

<h2>Final Thoughts</h2>
<p>Start small. Pick one or two habits and track them for 30 days. Once they become automatic, add more. The <a href="https://companymaster.gumroad.com/l/habit-tracker" target="_blank" rel="noopener">Habit Tracker</a> makes it easy to scale from a few habits to a complete personal growth system.</p>
""",
        "products": [
            {"slug": "habit-tracker", "name": "Habit Tracker"},
            {"slug": "goal-setting", "name": "Goal Setting Workbook"},
            {"slug": "productivity-bundle", "name": "Productivity Pro Bundle"}
        ]
    },
    {
        "slug": "goal-setting-framework",
        "title": "The Ultimate Goal Setting Framework — Turn Your Dreams into Achievable Plans",
        "meta_desc": "Learn the proven goal setting framework used by high achievers. Includes OKRs, 90-day sprints, and weekly action plans with printable goal planners.",
        "h1": "The Ultimate Goal Setting Framework",
        "content": """
<p>Setting goals is easy. Achieving them is hard. The difference between dreamers and achievers isn't talent or luck — it's having a systematic framework for turning aspirations into actionable plans. In this article, we'll break down a proven goal-setting framework that works for career goals, fitness targets, financial objectives, and personal development.</p>

<h2>Why Most Goal Setting Fails</h2>
<p>Studies show that over 80% of New Year's resolutions fail by February. The main reasons? Goals are too vague, too ambitious, or lack a tracking system. Without a framework, even the most motivated people struggle to maintain momentum.</p>

<h2>The CompanyMaster Goal Setting Framework</h2>
<p>This framework combines OKRs (Objectives and Key Results) with 90-day sprints and weekly action plans. It's designed to bridge the gap between your big vision and daily actions.</p>

<h3>Step 1: Define Your Quarterly OKRs</h3>
<p>Start by setting 1-3 objectives for the quarter. Each objective should have 2-3 measurable key results. For example:</p>
<ul>
<li><strong>Objective:</strong> Grow my freelance business</li>
<li><strong>Key Results:</strong> Land 3 new clients, increase monthly revenue by 30%, build a referral system</li>
</ul>
<p>The <strong>Goal Setting Workbook</strong> includes dedicated pages for defining and tracking your OKRs each quarter.</p>
<p><a href="https://companymaster.gumroad.com/l/goal-setting" target="_blank" rel="noopener">Get the Goal Setting Workbook →</a></p>

<h3>Step 2: Break Goals into 90-Day Sprints</h3>
<p>A 90-day sprint is the perfect time frame for making meaningful progress without losing focus. Each sprint should have a clear theme and specific deliverables. Break your quarterly OKRs into sprint-sized chunks and focus on one sprint at a time.</p>

<h3>Step 3: Create Weekly Action Plans</h3>
<p>Each week, identify 3-5 actions that will move your sprint forward. These should be specific, time-bound tasks that you can schedule into your calendar. At the end of each week, review what worked and adjust your plan for the next week.</p>

<h3>Step 4: Track Daily Habits That Support Your Goals</h3>
<p>Goals are achieved through daily habits. If your goal is to write a book, your daily habit might be writing 500 words. If your goal is to get fit, your daily habit might be a 30-minute workout. Use the <strong>Habit Tracker</strong> to stay consistent with these daily actions.</p>
<p><a href="https://companymaster.gumroad.com/l/habit-tracker" target="_blank" rel="noopener">Get the Habit Tracker →</a></p>

<h3>Step 5: Review and Adjust Monthly</h3>
<p>Schedule a monthly review session to assess your progress. Ask yourself: What's working? What's not? Do I need to adjust my key results? This reflection prevents you from spending months going in the wrong direction.</p>

<h2>The Complete System: Productivity Pro Bundle</h2>
<p>For the most comprehensive goal-setting system, the <strong>Productivity Pro Bundle</strong> includes the Goal Setting Workbook, Weekly Planner, Habit Tracker, Project Manager, and more — everything you need to turn your goals into reality.</p>
<p><a href="https://companymaster.gumroad.com/l/productivity-bundle" target="_blank" rel="noopener">Get the Productivity Pro Bundle →</a></p>

<h2>Final Thoughts</h2>
<p>Goal setting is a skill. Like any skill, it improves with practice and the right tools. Start with one goal, apply this framework, and use the <a href="https://companymaster.gumroad.com/l/goal-setting" target="_blank" rel="noopener">Goal Setting Workbook</a> to track your progress. You'll be amazed at what you can achieve in just 90 days.</p>
""",
        "products": [
            {"slug": "goal-setting", "name": "Goal Setting Workbook"},
            {"slug": "productivity-bundle", "name": "Productivity Pro Bundle"},
            {"slug": "habit-tracker", "name": "Habit Tracker"}
        ]
    },
    {
        "slug": "effective-meeting-notes",
        "title": "How to Take Effective Meeting Notes — Templates and Techniques for Better Meetings",
        "meta_desc": "Master the art of taking effective meeting notes. Learn proven techniques, templates, and tools to capture action items and decisions from every meeting.",
        "h1": "How to Take Effective Meeting Notes",
        "content": """
<p>Meetings are unavoidable in professional life, but poorly managed meetings waste billions of dollars in productivity every year. One of the simplest ways to improve meeting productivity is to take better notes. Effective meeting notes ensure that decisions are documented, action items are assigned, and nothing falls through the cracks.</p>

<p>In this guide, we'll share proven techniques for taking meeting notes and introduce templates that make the process effortless.</p>

<h2>Why Meeting Notes Matter</h2>
<p>Good meeting notes serve several critical purposes. They create a record of decisions made, provide accountability for action items, help absent team members catch up, and serve as a reference for future discussions. Without notes, meetings become forgettable conversations rather than productive working sessions.</p>

<h2>The PAR Method for Meeting Notes</h2>
<p>One of the most effective frameworks for meeting notes is the <strong>PAR Method</strong>: Purpose, Agenda, Results.</p>

<h3>Purpose</h3>
<p>Before the meeting, write down the purpose. Why is this meeting happening? What outcome is needed? Share this with attendees in advance so everyone comes prepared.</p>

<h3>Agenda</h3>
<p>List the topics to be discussed with time allocations. A good agenda prevents meetings from going off track and ensures all important topics are covered.</p>

<h3>Results</h3>
<p>After the meeting, document: decisions made, action items (with owners and deadlines), and open questions that need follow-up. This is the most important part — it's what makes meetings productive.</p>

<p>The <strong>Meeting Notes Template</strong> is built around the PAR Method and includes dedicated sections for each part.</p>
<p><a href="https://companymaster.gumroad.com/l/meeting-notes" target="_blank" rel="noopener">Get the Meeting Notes Template →</a></p>

<h2>Tips for Better Meeting Notes</h2>
<ul>
<li><strong>Prepare in advance:</strong> Review the agenda before the meeting and set up your note-taking template</li>
<li><strong>Focus on decisions, not verbatim:</strong> Don't try to capture everything said — focus on decisions, action items, and key points</li>
<li><strong>Assign action items clearly:</strong> Every action item should have an owner and a deadline</li>
<li><strong>Distribute notes promptly:</strong> Send notes within 24 hours while the discussion is still fresh</li>
<li><strong>Use a consistent format:</strong> A template ensures you never miss important elements</li>
</ul>

<h2>Integrate Meeting Notes with Your Weekly Planning</h2>
<p>Meeting notes don't exist in isolation. Action items from meetings should feed directly into your weekly plan. The <strong>Ultimate Weekly Planner</strong> has dedicated space for weekly priorities and tasks, making it easy to transfer action items from your meeting notes into your planning system.</p>
<p><a href="https://companymaster.gumroad.com/l/weekly-planner" target="_blank" rel="noopener">Get the Ultimate Weekly Planner →</a></p>

<h2>Create a Meeting Notes Habit</h2>
<p>Like any productivity practice, taking good meeting notes becomes easier with consistency. Use the <strong>Habit Tracker</strong> to build a habit of preparing before meetings and distributing notes afterward. Within a few weeks, it will become second nature.</p>
<p><a href="https://companymaster.gumroad.com/l/habit-tracker" target="_blank" rel="noopener">Get the Habit Tracker →</a></p>

<h2>Final Thoughts</h2>
<p>Effective meeting notes transform meetings from time-wasters into productive working sessions. Start using the PAR method today, grab the <a href="https://companymaster.gumroad.com/l/meeting-notes" target="_blank" rel="noopener">Meeting Notes Template</a>, and watch your meeting productivity improve dramatically.</p>
""",
        "products": [
            {"slug": "meeting-notes", "name": "Meeting Notes Template"},
            {"slug": "weekly-planner", "name": "Ultimate Weekly Planner"},
            {"slug": "habit-tracker", "name": "Habit Tracker"}
        ]
    }
]

# ─── CONFIG ───────────────────────────────────────────────
BASE_DIR = Path("/opt/data/projetos/saas")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "saas.db"
VISITS_DB_PATH = DATA_DIR / "visits.db"
PORT = 8080

# ─── DATABASE ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            email TEXT,
            plan TEXT DEFAULT 'free',
            credits INTEGER DEFAULT 100,
            created_at TEXT DEFAULT (datetime('now')),
            last_used TEXT
        );
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            endpoint TEXT,
            timestamp TEXT DEFAULT (datetime('now')),
            status INTEGER,
            credits_used INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT DEFAULT (datetime('now')),
            source TEXT,
            amount_usd REAL,
            user_api_key TEXT
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            plan TEXT,
            status TEXT DEFAULT 'active',
            started_at TEXT DEFAULT (datetime('now')),
            amount_usd REAL
        );
        CREATE TABLE IF NOT EXISTS url_shortener (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            api_key TEXT,
            clicks INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def generate_api_key():
    return "cm_" + secrets.token_hex(16)

def create_user(conn, email=None, plan="free", initial_credits=100):
    api_key = generate_api_key()
    conn.execute(
        "INSERT INTO users (api_key, email, plan, credits) VALUES (?,?,?,?)",
        (api_key, email, plan, initial_credits)
    )
    conn.commit()
    return api_key

# ─── VISIT TRACKING ───────────────────────────────────────
def init_visits_db():
    conn = sqlite3.connect(str(VISITS_DB_PATH))
    conn.execute("CREATE TABLE IF NOT EXISTS visits (route TEXT PRIMARY KEY, count INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()
    return VISITS_DB_PATH

def track_visit(route):
    """Increment visit counter for a given route. Non-blocking on errors."""
    try:
        conn = sqlite3.connect(str(VISITS_DB_PATH))
        conn.execute("INSERT OR IGNORE INTO visits (route, count) VALUES (?, 0)", (route,))
        conn.execute("UPDATE visits SET count = count + 1 WHERE route = ?", (route,))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Never break the app for visit tracking

# ─── SAAS: URL Shortener ─────────────────────────────────
class URLShortener:
    """Serviço de encurtamento de URL — MVP monetizável."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def shorten(self, original_url, api_key=None):
        # Gerar código curto
        code = secrets.token_hex(4)  # 8 caracteres
        self.conn.execute(
            "INSERT INTO url_shortener (short_code, original_url, api_key) VALUES (?,?,?)",
            (code, original_url, api_key)
        )
        self.conn.commit()
        return {
            "short_code": code,
            "short_url": f"http://localhost:{PORT}/s/{code}",
            "original_url": original_url
        }
    
    def lookup(self, code):
        cur = self.conn.execute(
            "SELECT original_url, clicks FROM url_shortener WHERE short_code = ?",
            (code,)
        )
        row = cur.fetchone()
        if row:
            self.conn.execute(
                "UPDATE url_shortener SET clicks = clicks + 1 WHERE short_code = ?",
                (code,)
            )
            self.conn.commit()
            return row[0]
        return None
    
    def stats(self, code):
        cur = self.conn.execute(
            "SELECT short_code, original_url, clicks, created_at FROM url_shortener WHERE short_code = ?",
            (code,)
        )
        row = cur.fetchone()
        if row:
            return {
                "short_code": row[0],
                "original_url": row[1],
                "clicks": row[2],
                "created_at": row[3]
            }
        return None

# ─── SAAS: QR Code Generator ──────────────────────────────
# (usando API externa gratuita — Google Charts)
def generate_qr(text, size=200):
    """Gera URL de QR code via Google Charts API (gratuito)."""
    import urllib.parse
    encoded = urllib.parse.quote(text.encode('utf-8'))
    return f"https://chart.googleapis.com/chart?chs={size}x{size}&cht=qr&chl={encoded}&choe=UTF-8"

# ─── SAAS: Text Tools ─────────────────────────────────────
class TextTools:
    """Ferramentas de processamento de texto monetizáveis."""
    
    @staticmethod
    def word_count(text):
        return {"words": len(text.split()), "chars": len(text), "lines": text.count('\n') + 1}
    
    @staticmethod
    def character_count(text):
        """Contagem detalhada: caracteres (com/sem espaços), palavras, linhas, parágrafos."""
        chars_total = len(text)
        chars_no_spaces = len(text.replace(' ', ''))
        words = len(text.split()) if text.strip() else 0
        lines = text.count('\n') + 1 if text else 1
        paragraphs = len([p for p in text.split('\n\n') if p.strip()]) if text.strip() else 0
        return {
            "characters_total": chars_total,
            "characters_no_spaces": chars_no_spaces,
            "words": words,
            "lines": lines,
            "paragraphs": paragraphs
        }
    
    @staticmethod
    def markdown_to_html(text):
        # Conversor básico (MVP)
        import re
        html = text
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        html = re.sub(r'\n\n', '</p><p>', html)
        html = '<p>' + html + '</p>'
        return {"html": html}
    
    @staticmethod
    def slugify(text):
        import re, unicodedata
        slug = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return {"slug": slug}

# ─── HTTP SERVER ──────────────────────────────────────────
class SaaSHandler(BaseHTTPRequestHandler):
    conn = None  # Será setado externamente
    url_shortener = None
    
    def log_message(self, format, *args):
        pass  # Silent
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _check_api_key(self):
        """Verifica API key no header ou query param."""
        api_key = self.headers.get('X-API-Key', '')
        if not api_key:
            parsed = urlparse(self.path)
            api_key = parse_qs(parsed.query).get('api_key', [''])[0]
        if not api_key:
            return None
        
        cur = self.conn.execute(
            "SELECT api_key, plan, credits FROM users WHERE api_key = ?",
            (api_key,)
        )
        return cur.fetchone()
    
    def _serve_html(self, html, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _make_schema_org_json(self):
        """JSON-LD Organization schema for SEO."""
        return json.dumps({
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "CompanyMaster",
            "url": "https://companymaster.gumroad.com",
            "sameAs": [
                "https://bsky.app/profile/companymaster",
                "https://dev.to/companymaster"
            ]
        }, ensure_ascii=False)
    
    def _make_schema_products_json(self):
        """JSON-LD ItemList of Product schemas for SEO."""
        items = []
        for i, p in enumerate(PRODUCTS, 1):
            items.append({
                "@type": "ListItem",
                "position": i,
                "item": {
                    "@type": "Product",
                    "name": p['name'],
                    "description": p['desc'],
                    "url": f"https://companymaster.gumroad.com/l/{p['slug']}",
                    "offers": {
                        "@type": "Offer",
                        "price": p['price'],
                        "priceCurrency": "USD"
                    }
                }
            })
        return json.dumps({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "itemListElement": items
        }, ensure_ascii=False)
    
    def serve_products(self):
        """Render product catalog landing page."""
        cards_html = ''
        for i, p in enumerate(PRODUCTS):
            gumroad_url = f"https://companymaster.gumroad.com/l/{p['slug']}"
            price_str = f"${p['price']:.2f}" if p['price'] > 0 else "Free"
            cards_html += f'''
            <div class="product-card">
                <div class="product-category">{p['category']}</div>
                <h3 class="product-name">{p['name']}</h3>
                <p class="product-desc">{p['desc']}</p>
                <div class="product-footer">
                    <span class="product-price">{price_str}</span>
                    <a class="product-btn" href="{gumroad_url}" target="_blank" rel="noopener">View on Gumroad →</a>
                </div>
            </div>'''
        
        schema_org = self._make_schema_org_json()
        schema_prods = self._make_schema_products_json()
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CompanyMaster — Digital Products</title>
<meta name="description" content="Printable planners & digital tools to organize your life. Browse our catalog of {len(PRODUCTS)} premium digital planners, trackers, and organizers.">
<meta property="og:title" content="CompanyMaster — Digital Products">
<meta property="og:description" content="Printable planners & digital tools to organize your life. Browse our catalog of {len(PRODUCTS)} premium digital planners, trackers, and organizers.">
<meta property="og:url" content="https://companymaster-saas-production.up.railway.app/products">
<meta property="og:type" content="website">
<meta property="og:site_name" content="CompanyMaster">
<script type="application/ld+json">
{schema_org}
</script>
<script type="application/ld+json">
{schema_prods}
</script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 60px 0 40px; text-align: center; }}
header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
header p {{ font-size: 1.1rem; opacity: 0.85; max-width: 600px; margin: 0 auto; }}
header .subtitle {{ margin-top: 8px; font-size: 0.95rem; opacity: 0.7; }}
.products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; padding: 40px 0; }}
.product-card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; border: 1px solid #e8e8ec; }}
.product-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }}
.product-category {{ display: inline-block; background: #eef0f7; color: #0f3460; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 10px; border-radius: 20px; margin-bottom: 12px; align-self: flex-start; }}
.product-name {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 10px; line-height: 1.35; color: #1a1a2e; }}
.product-desc {{ font-size: 0.9rem; color: #555; margin-bottom: 16px; flex-grow: 1; }}
.product-footer {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #eee; padding-top: 16px; }}
.product-price {{ font-size: 1.25rem; font-weight: 700; color: #0f3460; }}
.product-btn {{ background: #0f3460; color: white; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: background 0.2s; }}
.product-btn:hover {{ background: #1a4a7a; }}
.count-badge {{ text-align: center; margin: 20px 0 0; font-size: 0.9rem; color: #777; }}
footer {{ background: #1a1a2e; color: #999; padding: 30px 0; text-align: center; margin-top: 40px; }}
footer a {{ color: #8ab4f8; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}
@media (max-width: 720px) {{
    header h1 {{ font-size: 1.8rem; }}
    .products-grid {{ grid-template-columns: 1fr; }}
    .product-footer {{ flex-direction: column; gap: 12px; align-items: stretch; text-align: center; }}
    .product-btn {{ text-align: center; }}
}}
</style>
</head>
<body>
<header>
    <div class="container">
        <h1>🏢 CompanyMaster — Digital Products</h1>
        <p>Printable planners &amp; digital tools to organize your life</p>
        <p class="subtitle">Browse our catalog of {len(PRODUCTS)} premium products on Gumroad</p>
    </div>
</header>
<main class="container">
    <div class="count-badge">Showing all {len(PRODUCTS)} products</div>
    <div class="products-grid">
        {cards_html}
    </div>
</main>
<footer>
    <div class="container">
        <p>© 2026 CompanyMaster — <a href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Visit our Gumroad Store</a> — <a href="/">API Home</a></p>
        <p style="margin-top:8px;font-size:0.8rem;">All products are digital downloads delivered via Gumroad</p>
    </div>
</footer>
</body>
</html>'''
        self._serve_html(html)
    
    def serve_blog_article(self, slug):
        """Render a single blog article page with SEO metadata and Gumroad product links."""
        # Find the article
        article = None
        for a in BLOG_ARTICLES:
            if a['slug'] == slug:
                article = a
                break
        if not article:
            self._send_json({"error": "Blog article not found"}, 404)
            return

        # Build product CTA cards
        product_cards = ''
        for p in article['products']:
            gumroad_url = f"https://companymaster.gumroad.com/l/{p['slug']}"
            product_cards += f'''
            <div class="blog-cta-card">
                <h4>{p['name']}</h4>
                <a class="blog-cta-btn" href="{gumroad_url}" target="_blank" rel="noopener">View on Gumroad →</a>
            </div>'''

        # Build blog link list
        blog_links = ''
        for a in BLOG_ARTICLES:
            active = ' class="blog-link-active"' if a['slug'] == slug else ''
            blog_links += f'<li><a href="/blog/{a["slug"]}"{active}>{a["h1"]}</a></li>'

        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Build JSON-LD separately to avoid f-string nesting issues
        article_schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article['title'],
            "description": article['meta_desc'],
            "url": f"https://companymaster-saas-production.up.railway.app/blog/{article['slug']}",
            "datePublished": today,
            "author": {
                "@type": "Organization",
                "name": "CompanyMaster"
            },
            "publisher": {
                "@type": "Organization",
                "name": "CompanyMaster",
                "url": "https://companymaster.gumroad.com"
            }
        }, ensure_ascii=False)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{article['title']} — CompanyMaster Blog</title>
<meta name="description" content="{article['meta_desc']}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://companymaster-saas-production.up.railway.app/blog/{article['slug']}">
<meta property="og:title" content="{article['title']}">
<meta property="og:description" content="{article['meta_desc']}">
<meta property="og:url" content="https://companymaster-saas-production.up.railway.app/blog/{article['slug']}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="CompanyMaster">
<meta property="article:published_time" content="{today}">
<script type="application/ld+json">
{article_schema}
</script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.8; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 0 20px; }}

/* Header */
.blog-header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 40px 0 30px; }}
.blog-header h1 {{ font-size: 2rem; margin-bottom: 6px; }}
.blog-header .blog-meta {{ font-size: 0.85rem; opacity: 0.7; }}
.blog-header .blog-back {{ display: inline-block; color: #8ab4f8; text-decoration: none; font-size: 0.9rem; margin-bottom: 12px; }}
.blog-header .blog-back:hover {{ text-decoration: underline; }}

/* Content */
.blog-content {{ background: white; border-radius: 0 0 12px 12px; padding: 40px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.blog-content h2 {{ font-size: 1.4rem; color: #0f3460; margin: 32px 0 12px; }}
.blog-content h3 {{ font-size: 1.15rem; color: #1a4a7a; margin: 24px 0 10px; }}
.blog-content p {{ margin-bottom: 16px; font-size: 1rem; color: #333; }}
.blog-content ul {{ margin: 10px 0 16px 24px; }}
.blog-content li {{ margin-bottom: 6px; font-size: 0.98rem; color: #444; }}
.blog-content a {{ color: #0f3460; font-weight: 600; text-decoration: none; border-bottom: 2px solid #d0d8e8; }}
.blog-content a:hover {{ color: #1a4a7a; border-bottom-color: #0f3460; }}
.blog-content strong {{ color: #1a1a2e; }}

/* Product CTAs */
.blog-ctas {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 30px 0 10px; }}
.blog-cta-card {{ background: #f0f4f8; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; text-align: center; }}
.blog-cta-card h4 {{ font-size: 0.95rem; color: #0f3460; margin-bottom: 10px; line-height: 1.3; }}
.blog-cta-btn {{ display: inline-block; background: #0f3460; color: white; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: background 0.2s; }}
.blog-cta-btn:hover {{ background: #1a4a7a; }}

/* Sidebar / Related */
.blog-sidebar {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.blog-sidebar h3 {{ font-size: 1.1rem; color: #0f3460; margin-bottom: 12px; }}
.blog-sidebar ul {{ list-style: none; }}
.blog-sidebar li {{ margin-bottom: 8px; }}
.blog-sidebar a {{ color: #0f3460; text-decoration: none; font-weight: 500; font-size: 0.95rem; }}
.blog-sidebar a:hover {{ text-decoration: underline; }}
.blog-sidebar .blog-link-active {{ font-weight: 700; color: #1a1a2e; }}

/* Footer */
footer {{ background: #1a1a2e; color: #999; padding: 30px 0; text-align: center; margin-top: 20px; }}
footer a {{ color: #8ab4f8; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}

@media (max-width: 720px) {{
    .blog-header h1 {{ font-size: 1.5rem; }}
    .blog-content {{ padding: 24px; }}
    .blog-ctas {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<header class="blog-header">
    <div class="container">
        <a class="blog-back" href="/blog">← Blog Home</a>
        <h1>{article['h1']}</h1>
        <p class="blog-meta">Published {today} · CompanyMaster Blog</p>
    </div>
</header>
<main class="container">
    <div class="blog-content">
        {article['content']}
        <div class="blog-ctas">
            {product_cards}
        </div>
    </div>
    <div class="blog-sidebar">
        <h3>📖 More Articles</h3>
        <ul>
            {blog_links}
        </ul>
    </div>
</main>
<footer>
    <div class="container">
        <p>© 2026 CompanyMaster — <a href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Gumroad Store</a> — <a href="/">Home</a> — <a href="/blog">Blog</a></p>
    </div>
</footer>
</body>
</html>'''
        self._serve_html(html)

    def serve_blog_index(self):
        """Render blog index page listing all articles."""
        schema_org = self._make_schema_org_json()

        cards = ''
        for a in BLOG_ARTICLES:
            # Truncate meta desc for card
            excerpt = a['meta_desc'][:120] + '...' if len(a['meta_desc']) > 120 else a['meta_desc']
            cards += f'''
            <div class="blog-card">
                <h2 class="blog-card-title"><a href="/blog/{a['slug']}">{a['h1']}</a></h2>
                <p class="blog-card-desc">{excerpt}</p>
                <a class="blog-card-link" href="/blog/{a['slug']}">Read More →</a>
            </div>'''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CompanyMaster Blog — Productivity Tips, Planners &amp; Printable Templates</title>
<meta name="description" content="Read the latest articles about productivity, digital planning, habit tracking, goal setting, and organization tips from CompanyMaster.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://companymaster-saas-production.up.railway.app/blog">
<meta property="og:title" content="CompanyMaster Blog — Productivity Tips &amp; Templates">
<meta property="og:description" content="Read the latest articles about productivity, digital planning, habit tracking, goal setting, and organization tips from CompanyMaster.">
<meta property="og:url" content="https://companymaster-saas-production.up.railway.app/blog">
<meta property="og:type" content="blog">
<meta property="og:site_name" content="CompanyMaster">
<script type="application/ld+json">
{schema_org}
</script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 0 20px; }}

header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 50px 0 35px; text-align: center; }}
header h1 {{ font-size: 2.2rem; margin-bottom: 8px; }}
header p {{ font-size: 1.05rem; opacity: 0.85; max-width: 600px; margin: 0 auto; }}
header .badge {{ display: inline-block; background: rgba(255,255,255,0.15); padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; margin-top: 10px; }}

.blog-grid {{ display: grid; gap: 18px; padding: 30px 0; }}
.blog-card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid #e8e8ec; }}
.blog-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }}
.blog-card-title {{ font-size: 1.2rem; margin-bottom: 8px; }}
.blog-card-title a {{ color: #0f3460; text-decoration: none; }}
.blog-card-title a:hover {{ text-decoration: underline; }}
.blog-card-desc {{ font-size: 0.95rem; color: #555; margin-bottom: 14px; }}
.blog-card-link {{ color: #0f3460; font-weight: 600; font-size: 0.9rem; text-decoration: none; }}
.blog-card-link:hover {{ text-decoration: underline; }}

.store-cta {{ background: linear-gradient(135deg, #0f3460 0%, #1a4a7a 100%); color: white; border-radius: 16px; padding: 28px; margin: 0 0 30px; text-align: center; }}
.store-cta h2 {{ font-size: 1.4rem; margin-bottom: 8px; }}
.store-cta p {{ font-size: 0.95rem; opacity: 0.9; margin-bottom: 16px; }}
.store-cta .btn {{ display: inline-block; background: #ff6b35; color: white; padding: 10px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 0.95rem; transition: background 0.2s; }}
.store-cta .btn:hover {{ background: #e85d2c; }}

footer {{ background: #1a1a2e; color: #999; padding: 30px 0; text-align: center; margin-top: 20px; }}
footer a {{ color: #8ab4f8; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}

@media (max-width: 720px) {{
    header h1 {{ font-size: 1.6rem; }}
}}
</style>
</head>
<body>
<header>
    <div class="container">
        <h1>📝 CompanyMaster Blog</h1>
        <p>Productivity tips, planning guides, and organization strategies</p>
        <span class="badge">{len(BLOG_ARTICLES)} articles</span>
    </div>
</header>
<main class="container">
    <div class="store-cta">
        <h2>🛍️ Browse Our Digital Products</h2>
        <p>Printable planners, habit trackers, and organization tools — all on Gumroad</p>
        <a class="btn" href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Visit Gumroad Store →</a>
    </div>
    <div class="blog-grid">
        {cards}
    </div>
</main>
<footer>
    <div class="container">
        <p>© 2026 CompanyMaster — <a href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Gumroad Store</a> — <a href="/">Home</a> — <a href="/products">All Products</a></p>
    </div>
</footer>
</body>
</html>'''
        self._serve_html(html)

    def serve_homepage(self):
        """Render homepage with Organization JSON-LD, visitor counter, and Gumroad CTAs."""
        schema_org = self._make_schema_org_json()

        # Get visitor count for the homepage
        visitor_count = 0
        try:
            conn = sqlite3.connect(str(VISITS_DB_PATH))
            cur = conn.execute("SELECT count FROM visits WHERE route = '/'")
            row = cur.fetchone()
            if row:
                visitor_count = row[0]
            conn.close()
        except Exception:
            pass

        # Featured products (one from each major category)
        featured_slugs = ['bxssj', 'uzbmvd', 'hfwqoa', 'jptszh', 'vmpnry', 'bfprwg']
        featured_products = [p for p in PRODUCTS if p['slug'] in featured_slugs]

        featured_cards = ''
        for p in featured_products:
            gumroad_url = f"https://companymaster.gumroad.com/l/{p['slug']}"
            price_str = f"${p['price']:.2f}" if p['price'] > 0 else "Free"
            featured_cards += f'''
            <div class="featured-card">
                <span class="featured-cat">{p['category']}</span>
                <h3>{p['name']}</h3>
                <div class="featured-footer">
                    <span class="featured-price">{price_str}</span>
                    <a class="small-btn" href="{gumroad_url}" target="_blank" rel="noopener">Buy →</a>
                </div>
            </div>'''

        total_products = len(PRODUCTS)

        # Blog links for homepage
        blog_links = ''
        for a in BLOG_ARTICLES:
            blog_links += f'<li><a href="/blog/{a["slug"]}">{a["h1"]}</a></li>'

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CompanyMaster — Digital Products &amp; SaaS Tools</title>
<meta name="description" content="CompanyMaster: Printable planners, trackers &amp; organizers on Gumroad + free SaaS API tools (URL shortener, QR code generator, text tools).">
<meta property="og:title" content="CompanyMaster — Digital Products &amp; SaaS Tools">
<meta property="og:description" content="Printable planners, trackers &amp; organizers on Gumroad + free SaaS API tools (URL shortener, QR code generator, text tools).">
<meta property="og:url" content="https://companymaster-saas-production.up.railway.app/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="CompanyMaster">
<script type="application/ld+json">
{schema_org}
</script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
.container {{ max-width: 900px; margin: 0 auto; padding: 0 20px; }}

/* Header */
header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 60px 0 40px; text-align: center; }}
header h1 {{ font-size: 2.5rem; margin-bottom: 8px; }}
header p {{ font-size: 1.15rem; opacity: 0.9; max-width: 650px; margin: 0 auto; }}
header .badge {{ display: inline-block; background: rgba(255,255,255,0.15); padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; margin-top: 12px; }}

/* Section titles */
.section-title {{ font-size: 1.5rem; margin: 36px 0 6px; color: #1a1a2e; }}
.section-subtitle {{ font-size: 0.95rem; color: #666; margin-bottom: 20px; }}

/* Store Hero Card */
.store-hero {{ background: linear-gradient(135deg, #0f3460 0%, #1a4a7a 100%); color: white; border-radius: 16px; padding: 36px; margin: 24px 0 32px; text-align: center; box-shadow: 0 4px 16px rgba(15,52,96,0.25); }}
.store-hero h2 {{ font-size: 1.7rem; margin-bottom: 10px; }}
.store-hero p {{ font-size: 1rem; opacity: 0.9; max-width: 600px; margin: 0 auto 20px; }}
.store-hero .btn-group {{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }}
.store-hero .btn-primary {{ display: inline-block; background: #ff6b35; color: white; padding: 12px 32px; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 1rem; transition: background 0.2s, transform 0.1s; }}
.store-hero .btn-primary:hover {{ background: #e85d2c; transform: translateY(-1px); }}
.store-hero .btn-secondary {{ display: inline-block; background: rgba(255,255,255,0.2); color: white; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 1rem; transition: background 0.2s; border: 1px solid rgba(255,255,255,0.3); }}
.store-hero .btn-secondary:hover {{ background: rgba(255,255,255,0.3); }}

/* Featured Products Grid */
.featured-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 0 0 8px; }}
.featured-card {{ background: white; border-radius: 12px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; border: 1px solid #e8e8ec; }}
.featured-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }}
.featured-cat {{ display: inline-block; background: #eef0f7; color: #0f3460; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; border-radius: 20px; margin-bottom: 10px; align-self: flex-start; }}
.featured-card h3 {{ font-size: 0.9rem; font-weight: 600; margin-bottom: 12px; line-height: 1.3; color: #1a1a2e; flex-grow: 1; }}
.featured-footer {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #eee; padding-top: 12px; }}
.featured-price {{ font-weight: 700; color: #0f3460; font-size: 1rem; }}
.small-btn {{ background: #0f3460; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 600; transition: background 0.2s; }}
.small-btn {{ background: #0f3460; }}
.small-btn:hover {{ background: #1a4a7a; }}

/* API Card */
.card {{ background: white; border-radius: 12px; padding: 24px; margin: 24px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.card h2 {{ font-size: 1.3rem; margin-bottom: 12px; color: #0f3460; }}
.card ul {{ list-style: none; }}
.card li {{ padding: 6px 0; font-size: 0.95rem; }}
.card li a {{ color: #0f3460; text-decoration: none; font-weight: 500; }}
.card li a:hover {{ text-decoration: underline; }}
.endpoints {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.endpoint-item {{ background: #f0f4f8; padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; }}
.endpoint-item code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; }}
.btn {{ display: inline-block; background: #0f3460; color: white; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 8px; }}
.btn:hover {{ background: #1a4a7a; }}

/* Visitor Counter */
.visitor-count {{ text-align: center; margin: 10px 0; font-size: 0.85rem; color: #888; }}

/* Footer */
footer {{ background: #1a1a2e; color: #999; padding: 30px 0; text-align: center; margin-top: 40px; }}
footer a {{ color: #8ab4f8; text-decoration: none; }}
footer a:hover {{ text-decoration: underline; }}

@media (max-width: 720px) {{
    header h1 {{ font-size: 1.8rem; }}
    .featured-grid {{ grid-template-columns: 1fr; }}
    .endpoints {{ grid-template-columns: 1fr; }}
    .store-hero {{ padding: 24px 16px; }}
    .store-hero .btn-group {{ flex-direction: column; align-items: center; }}
}}
</style>
</head>
<body>
<header>
    <div class="container">
        <h1>🏢 CompanyMaster</h1>
        <p>Printable planners, digital organizers &amp; free SaaS API tools</p>
        <span class="badge">{total_products} products on Gumroad</span>
    </div>
</header>
<main class="container">
    <!-- Gumroad Store Hero -->
    <div class="store-hero">
        <h2>🛍️ Digital Products Store</h2>
        <p>Premium printable planners, trackers, and organizers to supercharge your productivity, health, finances, and daily life — all available on Gumroad.</p>
        <div class="btn-group">
            <a class="btn-primary" href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Visit Gumroad Store →</a>
            <a class="btn-secondary" href="/products">Browse All {total_products} Products</a>
        </div>
    </div>

    <!-- Featured Products -->
    <h2 class="section-title">⭐ Featured Products</h2>
    <p class="section-subtitle">Top picks from our catalog — planners, trackers, bundles and more</p>
    <div class="featured-grid">
        {featured_cards}
    </div>

    <!-- Blog Section -->
    <div class="card" style="margin-top: 28px;">
        <h2>📝 Latest from the Blog</h2>
        <p style="margin-bottom:14px;">Productivity tips, planning guides, and organization strategies to help you get more done.</p>
        <ul>
            {blog_links}
        </ul>
        <a class="btn" href="/blog">Read All Articles →</a>
    </div>

    <!-- What We Offer -->
    <div class="card">
        <h2>📋 What We Offer</h2>
        <p style="margin-bottom:14px;">CompanyMaster has two sides — <strong>digital products</strong> for personal organization and <strong>SaaS API tools</strong> for developers:</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
            <div style="background:#f0f4f8;padding:16px;border-radius:10px;">
                <h3 style="font-size:1rem;color:#0f3460;margin-bottom:6px;">🛍️ Gumroad Store</h3>
                <ul style="list-style:none;font-size:0.9rem;">
                    <li>📅 Planners (weekly, monthly, yearly)</li>
                    <li>💰 Budget &amp; finance trackers</li>
                    <li>🏃 Health &amp; fitness planners</li>
                    <li>👶 Baby &amp; parenting logs</li>
                    <li>✅ Habit &amp; goal trackers</li>
                    <li>📦 Value bundles (save up to 60%)</li>
                </ul>
            </div>
            <div style="background:#f0f4f8;padding:16px;border-radius:10px;">
                <h3 style="font-size:1rem;color:#0f3460;margin-bottom:6px;">🚀 SaaS API Tools</h3>
                <ul style="list-style:none;font-size:0.9rem;">
                    <li>🔗 URL shortener</li>
                    <li>📱 QR code generator</li>
                    <li>📝 Text tools (word count, markdown)</li>
                    <li>🔑 Free API key system</li>
                    <li>📊 Usage tracking included</li>
                    <li>⚡ Always-free tier available</li>
                </ul>
            </div>
        </div>
    </div>

    <!-- API Endpoints -->
    <div class="card">
        <h2>🚀 API Endpoints</h2>
        <div class="endpoints">
            <div class="endpoint-item"><code>GET /health</code> — Health check</div>
            <div class="endpoint-item"><code>POST /register</code> — Create API key</div>
            <div class="endpoint-item"><code>GET /shorten</code> — Shorten URL</div>
            <div class="endpoint-item"><code>GET /qr</code> — QR code generator</div>
            <div class="endpoint-item"><code>GET /tools/wordcount</code> — Word count</div>
            <div class="endpoint-item"><code>GET /tools/charactercount</code> — Character count</div>
            <div class="endpoint-item"><code>GET /tools/md2html</code> — Markdown to HTML</div>
            <div class="endpoint-item"><code>GET /tools/slugify</code> — URL slug generator</div>
            <div class="endpoint-item"><code>GET /products</code> — Product catalog ({total_products} products)</div>
            <div class="endpoint-item"><code>GET /catalog</code> — Product catalog view</div>
            <div class="endpoint-item"><code>GET /blog</code> — Blog index ({len(BLOG_ARTICLES)} articles)</div>
        </div>
        <a class="btn" href="/products">Browse Products →</a>
    </div>

    <!-- Visitor Counter -->
    <div class="visitor-count">
        👀 {visitor_count}+ visitors so far
    </div>
</main>
<footer>
    <div class="container">
        <p>© 2026 CompanyMaster — <a href="https://companymaster.gumroad.com" target="_blank" rel="noopener">Gumroad Store</a> — <a href="/products">All Products</a> — <a href="/blog">Blog</a> — <a href="/privacy">Privacy</a></p>
        <p style="margin-top:8px;font-size:0.8rem;">All products are digital downloads delivered via Gumroad</p>
    </div>
</footer>
</body>
</html>'''
        self._serve_html(html)
    
    def serve_sitemap(self):
        """Generate XML sitemap."""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        static_urls = [
            '/', '/products', '/catalog', '/shorten', '/qr',
            '/tools/wordcount', '/tools/charactercount', '/tools/md2html', '/tools/slugify',
            '/blog'
        ]
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        for u in static_urls:
            lines.append(f'  <url><loc>https://companymaster-saas-production.up.railway.app{u}</loc><lastmod>{today}</lastmod></url>')
        for a in BLOG_ARTICLES:
            lines.append(f'  <url><loc>https://companymaster-saas-production.up.railway.app/blog/{a["slug"]}</loc><lastmod>{today}</lastmod></url>')
        for p in PRODUCTS:
            lines.append(f'  <url><loc>https://companymaster.gumroad.com/l/{p["slug"]}</loc><lastmod>{today}</lastmod></url>')
        gumroad_path = Path('/opt/data/state/gumroad.json')
        if gumroad_path.exists():
            try:
                gumroad_data = json.loads(gumroad_path.read_text(encoding='utf-8'))
                # gumroad.json has aggregate data only; individual products come from PRODUCTS list
                pass
            except (json.JSONDecodeError, OSError):
                pass
        lines.append('</urlset>')
        xml = '\n'.join(lines)
        self.send_response(200)
        self.send_header('Content-Type', 'application/xml; charset=utf-8')
        self.end_headers()
        self.wfile.write(xml.encode('utf-8'))
    
    def serve_robots(self):
        """Generate robots.txt with Sitemap directive."""
        text = 'User-agent: *\nSitemap: https://companymaster-saas-production.up.railway.app/sitemap.xml\n'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(text.encode('utf-8'))
    
    def serve_stats_json(self):
        """Return visit counts as JSON."""
        try:
            conn = sqlite3.connect(str(VISITS_DB_PATH))
            cur = conn.execute("SELECT route, count FROM visits ORDER BY count DESC")
            rows = cur.fetchall()
            conn.close()
            data = {row[0]: row[1] for row in rows}
        except Exception:
            data = {"error": "Stats unavailable"}
        self._send_json(data)
    
    def serve_stats_html(self):
        """Render visit stats as HTML table."""
        try:
            conn = sqlite3.connect(str(VISITS_DB_PATH))
            cur = conn.execute("SELECT route, count FROM visits ORDER BY count DESC")
            rows = cur.fetchall()
            conn.close()
        except Exception:
            rows = []
        
        html_rows = ""
        total_visits = 0
        for route, count in rows:
            html_rows += f"<tr><td>{route}</td><td>{count}</td></tr>\n"
            total_visits += count
        
        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CompanyMaster — Admin Stats</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a2e; line-height: 1.6; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #0f3460; margin-bottom: 8px; }}
.summary {{ display: flex; gap: 20px; margin: 20px 0; }}
.summary-card {{ background: white; border-radius: 10px; padding: 16px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); flex: 1; text-align: center; }}
.summary-card .number {{ font-size: 2rem; font-weight: 700; color: #0f3460; }}
.summary-card .label {{ font-size: 0.85rem; color: #666; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
th {{ background: #0f3460; color: white; padding: 12px 16px; text-align: left; font-size: 0.9rem; }}
td {{ padding: 10px 16px; border-bottom: 1px solid #eee; }}
tr:hover td {{ background: #f0f4f8; }}
tr:last-child td {{ border-bottom: none; }}
.footer {{ margin-top: 20px; text-align: center; }}
.footer a {{ color: #0f3460; text-decoration: none; font-weight: 500; }}
.footer a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="container">
<h1>📊 Admin — Visit Stats</h1>
<p style="color:#666;">Tracking de visitas por rota</p>
<div class="summary">
<div class="summary-card">
<div class="number">{len(rows)}</div>
<div class="label">Rotas</div>
</div>
<div class="summary-card">
<div class="number">{total_visits}</div>
<div class="label">Total de Visitas</div>
</div>
</div>
<table>
<thead><tr><th>Rota</th><th>Visitas</th></tr></thead>
<tbody>
{html_rows}
</tbody>
</table>
<div class="footer">
<p><a href="/">← Voltar ao início</a> &nbsp;|&nbsp; <a href="/stats">📋 JSON</a></p>
</div>
</div>
</body>
</html>'''
        self._serve_html(html)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        
        # Track visit for this route
        route = path if path else '/'
        track_visit(route)
        
        # Homepage
        if path in ('', '/'):
            return self.serve_homepage()
        
        # Health check
        if path == '/health':
            self._send_json({
                "service": "CompanyMaster SaaS",
                "version": "0.1.0",
                "status": "running",
                "endpoints": ["/shorten", "/qr", "/tools/wordcount", "/tools/md2html", "/tools/slugify", "/tools/charactercount", "/products", "/catalog"]
            })
            return
        
        # Sitemap
        if path == '/sitemap.xml':
            return self.serve_sitemap()
        
        # Robots.txt
        if path == '/robots.txt':
            return self.serve_robots()
        
        # Privacy Policy
        if path in ('/privacy', '/privacy/companymaster'):
            html = PRIVACY_POLICY_PATH.read_text(encoding='utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        # Product Catalog (Gumroad showcase)
        if path in ('/products', '/catalog'):
            return self.serve_products()

        # URL Shortener redirect
        if path.startswith('/s/'):
            code = path[3:]
            original = self.url_shortener.lookup(code)
            if original:
                self.send_response(302)
                self.send_header('Location', original)
                self.end_headers()
            else:
                self._send_json({"error": "Short URL not found"}, 404)
            return
        
        # Shorten via GET
        if path == '/shorten':
            params = parse_qs(parsed.query)
            url = params.get('url', [''])[0]
            if not url:
                self._send_json({"error": "Missing 'url' parameter"}, 400)
                return
            result = self.url_shortener.shorten(url)
            self._send_json(result)
            return
        
        # QR Code
        if path == '/qr':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            size = int(params.get('size', ['200'])[0])
            if not text:
                self._send_json({"error": "Missing 'text' parameter"}, 400)
                return
            qr_url = generate_qr(text, size)
            self._send_json({"qr_url": qr_url, "text": text, "size": size})
            return
        
        # Text tools
        if path == '/tools/wordcount':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.word_count(text)
            self._send_json(result)
            return
        
        if path == '/tools/md2html':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.markdown_to_html(text)
            self._send_json(result)
            return
        
        if path == '/tools/slugify':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.slugify(text)
            self._send_json(result)
            return
        
        # Character count
        if path == '/tools/charactercount':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.character_count(text)
            self._send_json(result)
            return
        
        # Stats
        if path.startswith('/stats/'):
            code = path[7:]
            stats = self.url_shortener.stats(code)
            if stats:
                self._send_json(stats)
            else:
                self._send_json({"error": "Not found"}, 404)
            return
        
        # Visit stats (JSON)
        if path == '/stats':
            return self.serve_stats_json()
        
        # Admin visit stats (HTML)
        if path == '/admin/stats':
            return self.serve_stats_html()
        
        # Blog
        if path == '/blog':
            return self.serve_blog_index()
        
        if path.startswith('/blog/'):
            slug = path[6:]  # Remove '/blog/'
            if slug:
                return self.serve_blog_article(slug)
        
        self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length else '{}'
        
        try:
            data = json.loads(body)
        except:
            data = {}
        
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        
        # Track visit for this route
        track_visit(path if path else '/')
        
        # Create API key
        if path == '/register':
            email = data.get('email', '')
            plan = data.get('plan', 'free')
            api_key = create_user(self.conn, email, plan)
            self._send_json({
                "api_key": api_key,
                "plan": plan,
                "message": "Save this API key! It won't be shown again."
            }, 201)
            return
        
        # Shorten via POST
        if path == '/shorten':
            url = data.get('url', '')
            if not url:
                self._send_json({"error": "Missing 'url'"}, 400)
                return
            api_key = data.get('api_key', '')
            result = self.url_shortener.shorten(url, api_key if api_key else None)
            self._send_json(result, 201)
            return
        
        self._send_json({"error": "Not found"}, 404)

def run_server(port=8080):
    conn = init_db()
    init_visits_db()
    
    # Criar usuário demo se não existir
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        demo_key = create_user(conn, "demo@companymaster.ai", "demo", 9999)
        print(f"\n🔑 Demo API Key: {demo_key}")
    
    SaaSHandler.conn = conn
    SaaSHandler.url_shortener = URLShortener(conn)
    
    server = HTTPServer(('0.0.0.0', port), SaaSHandler)
    print(f"\n🚀 CompanyMaster SaaS running on http://0.0.0.0:{port}")
    print(f"📋 Endpoints:")
    print(f"   GET  /health            — Health check")
    print(f"   POST /register          — Create API key")
    print(f"   GET  /shorten?url=...   — Shorten URL")
    print(f"   GET  /s/{'{code}'}          — Redirect to original URL")
    print(f"   GET  /qr?text=...       — Generate QR code")
    print(f"   GET  /tools/wordcount   — Count words")
    print(f"   GET  /tools/md2html     — Markdown to HTML")
    print(f"   GET  /tools/charactercount — Character count (chars, words, lines, paragraphs)")
    print(f"   GET  /tools/slugify     — URL slug generator")
    print(f"   GET  /products          — Product catalog ({len(PRODUCTS)} products)")
    print(f"   GET  /blog              — Blog index ({len(BLOG_ARTICLES)} articles)")
    print(f"   GET  /blog/<slug>       — Blog article")
    print(f"\n💰 Monetization-ready: API key system, usage tracking, subscription plans")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.shutdown()
        conn.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
