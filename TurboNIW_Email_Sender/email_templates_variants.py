"""
Multi-variant email templates for TurboNIW outreach.
Rotates through different subjects and body texts to:
  1. Avoid spam filters and Google's repeated message detection
  2. Maintain authentic, peer-to-peer tone
  3. Share resources without being pushy
  4. Create positive impressions and good customer outreach

================================================================================
EMAIL WRITING GUIDELINES FOR FUTURE VARIANTS
================================================================================

CORE PRINCIPLES:
1. EMPATHY-DRIVEN: Show genuine understanding and empathy
   - We've been there (international PhD students)
   - We understand the challenges (expensive attorneys, overwhelming DIY)
   - We want to help because we experienced it ourselves
   - Use phrases like "I understand how challenging", "I remember how", "we know how"

2. PEER SUPPORT: Emphasize we're supporting our peers
   - We're former international PhD students helping other researchers
   - We built this because we went through the same experience
   - We're part of the same community
   - Use "we", "us", "our community", "fellow researchers"

3. STARTUP VALUE: Show we're a startup that values peer recommendations
   - We're a small team (former PhD students)
   - We value peer recommendations and referrals
   - We appreciate when people share it with others
   - We're always happy to show appreciation for referrals
   - Make it clear we're a startup, not a big corporation

4. IMPORTANCE TO RECIPIENTS: Show this is very important to many people
   - Many researchers need this
   - This can be life-changing for international researchers
   - It's a valuable resource for the community
   - Share it because many may need it

5. MAKE PEOPLE FEEL GOOD: Positive, warm, supportive tone
   - Compliment their work genuinely
   - Show respect for their research
   - Be warm and friendly
   - Make them feel valued and understood
   - End with positive wishes for their research

6. NO PRESSURE: Always emphasize no pressure
   - "No pressure at all"
   - "Just wanted to pass it along"
   - "Totally optional"
   - "Just sharing in case it's useful"
   - Make it feel like a genuine resource share, not a sales pitch

7. NATURAL LANGUAGE: Avoid AI-written patterns
   - Use commas and natural breaks (NO "---" separators)
   - Vary sentence structures
   - Use conversational, authentic language
   - Avoid repetitive patterns
   - Sound like a real person writing to a peer

8. CORE MESSAGE ELEMENTS (must include):
   - Personal introduction (Wen, former international PhD student)
   - Reference to their work (paper title)
   - Connection to NIW relevance (Critical and Emerging Technologies)
   - Our experience (went through NIW ourselves)
   - The problem (expensive attorneys vs overwhelming DIY)
   - Our solution (TurboNIW tool)
   - Why we built it (to help others, reduce stress)
   - Peer recommendations mention (we value referrals)
   - No pressure closing
   - Positive wishes for their research

9. TONE CHECKLIST:
   ✓ Empathetic and understanding
   ✓ Peer-to-peer, not corporate
   ✓ Warm and friendly
   ✓ Supportive and helpful
   ✓ Genuine and authentic
   ✓ Respectful of their work
   ✓ Community-focused
   ✓ Startup-friendly (values referrals)
   ✓ Makes recipient feel good
   ✓ No pressure, just helpful

10. AVOID:
   ✗ "---" separators (use commas or natural breaks)
   ✗ Corporate/sales language
   ✗ Pushy or aggressive tone
   ✗ Generic AI-written patterns
   ✗ Repetitive sentence structures
   ✗ Overly formal language
   ✗ Making it sound like a transaction

================================================================================
"""

import random

# ============================================================================
# SUBJECT LINE VARIANTS
# ============================================================================

SUBJECT_VARIANTS = [
    # Variant 1: Casual greeting
    "Greetings from Wen, a resource you might find helpful",
    
    # Variant 2: Simple and friendly
    "Hi from Wen, sharing a helpful NIW resource",
    
    # Variant 3: Resource-focused (not work-focused)
    "Hello from Wen, a resource for NIW applications",
    
    # Variant 4: Quick and chill
    "Quick hello and a resource to share",
    
    # Variant 5: Casual intro
    "Hi, Wen here, wanted to share something helpful",
    
    # Variant 6: Personal touch
    "Hello from Wen, sharing something that might help",
    
    # Variant 7: Research connection
    "Reaching out about your work and a resource",
    
    # Variant 8: Friendly intro
    "Hi there, Wen here with a quick note",
    
    # Variant 9: Community-focused
    "A resource for researchers like us",
    
    # Variant 10: Casual and warm
    "Hope you're doing well, wanted to share this",
    
    # Variant 11: Direct but friendly
    "Hi, thought this might be useful",
    
    # Variant 12: Peer-to-peer
    "From one researcher to another",
    
    # Variant 13: Simple connection
    "Hello, sharing a resource you might find helpful",
    
    # Variant 14: Warm greeting
    "Hi, hope this finds you well",
    
    # Variant 15: Community resource
    "A helpful tool for the research community",
    
    # Variant 16: Casual share
    "Quick note about a resource",
    
    # Variant 17: Friendly outreach
    "Hello from Wen, a quick share",
    
    # Variant 18: Research community
    "Something that might help with NIW",
    
    # Variant 19: Simple intro
    "Hi, wanted to share this with you",
    
    # Variant 20: Community support
    "A tool that might be helpful",
]


# ============================================================================
# EMAIL SIGNATURE
# ============================================================================

EMAIL_SIGNATURE = """
--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Personal Website: https://wenxie18.github.io/
LinkedIn: https://www.linkedin.com/in/vincexie/
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""

# ============================================================================
# EMAIL BODY VARIANTS
# ============================================================================

EMAIL_BODY_VARIANT_1 = """Hi {name},

I hope this email finds you well.

I came across your recent work titled "<em>{paper_title}</em>", and it caught my attention, particularly given how it relates to areas on the White House's Critical and Emerging Technologies list. For researchers working in these fields, the National Interest Waiver (NIW) green card pathway can be a valuable option if they're considering opportunities in the U.S.

I'm Wen. I was an international PhD student myself, and after going through the NIW process firsthand, I understand how challenging it can be. Many people face a difficult choice: hiring an attorney can be very expensive, often beyond what's feasible for early career researchers, while the DIY route feels overwhelming because it's hard to know where to start, what forms to fill out, or what a strong application should look like.

That's why a few of us (former international PhD students) created a tool to help make this easier. It's called <strong>TurboNIW</strong>.

It provides petition letter drafts and completed forms, designed for people who want to handle NIW themselves but need a clearer starting point and guidance on the process. We built this because we know how stressful and uncertain this journey can be, and we wanted to help others navigate it with more confidence.

I'm sharing this in case it's useful to you, your students, or colleagues navigating this process. No pressure at all, just wanted to pass it along as a resource in case it helps. We also value peer recommendations, so if you know anyone who might benefit from this, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

As a resource for the community, our website also features the latest news and common Q&As about NIW immigration.

Feel free to reach out if you ever want to discuss the NIW process or compare experiences.

Best wishes with your research!

Best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>
--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_2 = """Hi {name},

I hope you're doing well!

I recently saw your work titled "<em>{paper_title}</em>" and found it quite interesting, especially in the context of U.S. immigration pathways for researchers. As someone whose research aligns with critical technology areas, you might already know that the National Interest Waiver (NIW) green card can be an important option for academics and researchers.

A bit about me: I'm Wen, a former international PhD student who went through the NIW process myself. One thing I remember clearly is how overwhelming it was. Many of us face a tough situation: attorney fees can be quite high, which makes it difficult for many researchers, while trying to do it yourself feels impossible without guidance on where to start or what the process should look like.

After finishing my degree, I teamed up with a few others (former PhD students) to build something that could help. We created <strong>TurboNIW</strong>, a DIY tool that generates petition drafts and completes forms.

It's meant to reduce the stress and uncertainty for people who want to handle NIW on their own but don't know where to begin. We know how challenging this process can be, and we wanted to create something that could help others navigate it with more confidence and less anxiety.

I wanted to share this with you in case it's helpful, either for yourself or for any international students/colleagues who might be dealing with NIW. Totally no pressure, just passing along a resource that might make things a bit easier for those who need it. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

Our website also serves as a community resource, with recent updates and frequently asked questions about NIW immigration.

Happy to chat more about the process anytime!

Best wishes with your research!

Best regards,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_3 = """Hi {name},

I hope this note finds you well.

I came across your recent work titled "<em>{paper_title}</em>". Given the areas you're researching, I thought it might be worth mentioning a resource related to NIW (National Interest Waiver) green cards, which can be relevant for researchers in emerging tech fields who are considering U.S. opportunities.

A little background: I'm Wen, and I used to be an international PhD student in the U.S. When I went through the NIW application process, I quickly realized how difficult the situation can be for many researchers. Attorney fees can be quite high, which makes it challenging for many of us, while the DIY path is confusing because there's no clear guide for beginners on where to start, what forms to fill out, or how to structure the application.

To help address this, a few of us who went through the same experience built a straightforward tool called <strong>TurboNIW</strong>.

It helps generate petition drafts and completed forms, giving people a solid starting point if they want to handle NIW themselves. We created this because we understand how stressful and uncertain this process can be, and we wanted to help others navigate it with more confidence.

I'm sharing this purely as a resource, if it's not relevant to you personally, maybe it's helpful for students or colleagues navigating this. No pressure at all. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

We also maintain our website as a community resource, where you can find the latest news and answers to common questions about NIW immigration.

Feel free to reach out if you ever want to discuss NIW or share insights from your own experience.

Best wishes with your research!

All the best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_4 = """Hi {name},

I hope you're having a good week.

I wanted to reach out because I recently came across your work titled "<em>{paper_title}</em>". It's genuinely impressive, and it reminded me of how many international researchers are working on technologies that align with the U.S. government's Critical and Emerging Technologies list, which can make NIW (National Interest Waiver) green card pathways quite relevant.

I'm Wen, a former international PhD student who went through the NIW process myself. One of the hardest parts for me was facing the reality that many of us encounter: attorney fees can be quite high, which isn't always feasible, while trying the DIY route feels overwhelming without proper guidance on where to start or what the process should look like.

After finishing my PhD, I worked with a few others who had similar experiences, and we built a tool to help people navigate this more easily. It's called <strong>TurboNIW</strong>.

The goal is to provide a petition draft and completed forms, designed for researchers who want to take control of their NIW application but need a clearer roadmap and guidance through the process. We know how challenging this journey can be, and we wanted to create something that could help reduce the stress and uncertainty.

I'm not pushing this at all, just sharing in case it's useful to you, your students, or colleagues who are dealing with NIW. If you're a professor or industry researcher, feel free to pass it along to anyone who might benefit. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

As part of our community support, our website includes recent news updates and a Q&A section covering NIW immigration topics.

Always happy to chat about the NIW process or compare notes!

Best wishes with your research!

Best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_5 = """Hi {name},

I hope this message finds you well.

I recently came across your work titled "<em>{paper_title}</em>", and it stood out to me, particularly because it touches on areas that fall under the U.S. Critical and Emerging Technologies framework. For researchers in these fields, the National Interest Waiver (NIW) green card can be a practical pathway worth considering.

A bit about myself: I'm Wen, and I used to be an international PhD student. I went through the NIW application process on my own, and I remember how challenging it was. Many researchers face a difficult situation: attorney fees can be quite high, which makes it hard for many of us, while trying to DIY it felt like navigating a maze without a map, not knowing where to start or what the process should look like.

After going through that experience, I teamed up with a few others (former PhD students) to create a tool that could make this process more accessible. We built <strong>TurboNIW</strong>.

It's a straightforward DIY tool that generates petition drafts and completes forms. The idea is to give people a solid starting point and clear guidance, reducing the stress and uncertainty that comes with navigating the process alone. We built this because we understand how overwhelming this can feel, and we wanted to help others who might be in the same situation.

I'm sharing this purely as a resource, if it's not relevant to you personally, perhaps it's useful for students or colleagues navigating NIW. No pressure whatsoever. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

Our website also provides community resources, including the latest NIW immigration news and answers to frequently asked questions.

Feel free to reach out anytime if you want to discuss the NIW process or exchange experiences!

Best wishes with your research!

Best regards,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_6 = """Hi {name},

Hope you're doing well.

I recently read your paper "<em>{paper_title}</em>" and found it really interesting. Your work touches on areas that are part of the U.S. Critical and Emerging Technologies list, which made me think about how National Interest Waiver (NIW) green cards can be relevant for researchers in these fields.

I'm Wen, and I was an international PhD student who went through the NIW process. What I remember most is how stuck many of us feel. On one hand, hiring an attorney costs a lot, often more than what's realistic for early career researchers. On the other hand, trying to do it yourself feels impossible when you don't know where to begin, what forms you need, or what a strong application looks like.

That's what led a few of us (former international PhD students) to build <strong>TurboNIW</strong>.

It's a tool that creates petition letter drafts and fills out forms, designed for people who want to handle their NIW application themselves but need a clear starting point and some guidance. We made this because we know how stressful and uncertain this process can be, and we wanted to help others feel more confident navigating it.

I'm sharing this in case it's useful to you or anyone in your network who might be dealing with NIW. No pressure at all, just wanted to pass it along. We also really appreciate when people share it with others who might benefit, and we're always happy to show our appreciation for referrals.

To help the community, we also keep our website updated with the latest NIW immigration news and answers to common questions.

Feel free to reach out if you want to talk about the NIW process or share experiences.

Best wishes with your research!

Best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_7 = """Hi {name},

I hope you're having a good week.

I came across your work "<em>{paper_title}</em>" and it caught my attention. Given the areas you're working in, I thought you might find it useful to know about NIW (National Interest Waiver) green cards, which can be a valuable option for researchers whose work aligns with critical technology areas.

Let me introduce myself: I'm Wen, a former international PhD student. When I was going through the NIW application, I realized how tough the situation is for many researchers. Attorney fees are often quite high, which makes it difficult for many of us, while the DIY approach feels overwhelming because there's no clear roadmap for beginners on where to start, what forms to complete, or how to structure everything.

After finishing my degree, I worked with a few others who had similar experiences, and together we created <strong>TurboNIW</strong>.

The idea is to provide petition drafts and completed forms, giving people a solid foundation if they want to handle NIW themselves. We built this because we understand how challenging and uncertain this journey can be, and we wanted to help others navigate it with more confidence and less stress.

I'm sharing this purely as a resource, in case it's helpful for you, your students, or colleagues who might be navigating NIW. Totally optional, just wanted to pass it along. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

Happy to chat more about NIW anytime!

Best wishes with your research!

Best regards,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_8 = """Hi {name},

Hope this message finds you well.

I wanted to reach out because I recently saw your work titled "<em>{paper_title}</em>". It's really impressive, and it reminded me of how many international researchers are working on technologies that fall under the U.S. government's Critical and Emerging Technologies framework, which can make National Interest Waiver (NIW) green card pathways quite relevant.

I'm Wen, and I used to be an international PhD student in the U.S. Going through the NIW process myself, I quickly learned how difficult it can be. Many of us face a challenging situation: attorney costs can be quite high, which isn't always feasible, while trying to do it yourself feels like you're lost without a guide, not knowing where to start or what the process should look like.

To help address this, a few of us who went through the same experience built a straightforward tool called <strong>TurboNIW</strong>.

It helps generate petition drafts and completed forms, designed for researchers who want to take control of their NIW application but need a clearer roadmap and guidance. We created this because we know how stressful and uncertain this process can be, and we wanted to help others feel more confident navigating it.

I'm not pushing this at all, just sharing in case it's useful to you, your students, or colleagues dealing with NIW. If you're a professor or work in industry, feel free to pass it along to anyone who might benefit. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

As a way to support the community, our website also includes recent news and frequently asked questions about NIW immigration.

Always happy to discuss the NIW process or compare notes!

Best wishes with your research!

All the best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_9 = """Hi {name},

I hope you're doing well.

I came across your recent paper "<em>{paper_title}</em>" and found it quite interesting, especially in the context of U.S. immigration pathways for researchers. As someone whose research aligns with critical technology areas, you might already be aware that the National Interest Waiver (NIW) green card can be an important option for academics and researchers.

A bit about me: I'm Wen, a former international PhD student who went through the NIW process myself. One thing that stands out from that experience is how overwhelming it can feel. Many of us face a tough situation: attorney fees can be quite high, which makes it difficult for many researchers, while trying to do it yourself feels impossible without guidance on where to start or what the process should look like.

After finishing my degree, I teamed up with a few others (former PhD students) to build something that could help. We created <strong>TurboNIW</strong>, a DIY tool that generates petition drafts and completes forms.

It's meant to reduce the stress and uncertainty for people who want to handle NIW on their own but don't know where to begin. We know how challenging this process can be, and we wanted to create something that could help others navigate it with more confidence and less anxiety.

I wanted to share this with you in case it's helpful, either for yourself or for any international students or colleagues who might be dealing with NIW. Totally no pressure, just passing along a resource that might make things a bit easier for those who need it. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

Our website also serves as a community resource where you can find the latest news and Q&As about NIW immigration.

Happy to chat more about the process anytime!

Best wishes with your research!

Best regards,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_10 = """Hi {name},

Hope this note finds you well.

I recently read your work "<em>{paper_title}</em>". Given the areas you're researching, I thought it might be worth mentioning a resource related to NIW (National Interest Waiver) green cards, which can be relevant for researchers in emerging tech fields who are considering U.S. opportunities.

A little background: I'm Wen, and I used to be an international PhD student in the U.S. When I went through the NIW application process, I quickly realized how difficult the situation can be for many researchers. Attorney fees can be quite high, which makes it challenging for many of us, while the DIY path is confusing because there's no clear guide for beginners on where to start, what forms to fill out, or how to structure the application.

To help address this, a few of us who went through the same experience built a straightforward tool called <strong>TurboNIW</strong>.

It helps generate petition drafts and completed forms, giving people a solid starting point if they want to handle NIW themselves. We created this because we understand how stressful and uncertain this process can be, and we wanted to help others navigate it with more confidence.

I'm sharing this purely as a resource. If it's not relevant to you personally, maybe it's helpful for students or colleagues navigating this. No pressure at all. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

We also maintain our website with community resources, including recent news and common Q&As about NIW immigration.

Feel free to reach out if you ever want to discuss NIW or share insights from your own experience.

Best wishes with your research!

All the best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_11 = """Hi {name},

I hope you're having a good week.

I wanted to reach out because I recently came across your work titled "<em>{paper_title}</em>". It's genuinely impressive, and it reminded me of how many international researchers are working on technologies that align with the U.S. government's Critical and Emerging Technologies list, which can make NIW (National Interest Waiver) green card pathways quite relevant.

I'm Wen, a former international PhD student who went through the NIW process myself. One of the hardest parts for me was facing the reality that many of us encounter: attorney fees can be quite high, which isn't always feasible, while trying the DIY route feels overwhelming without proper guidance on where to start or what the process should look like.

After finishing my PhD, I worked with a few others who had similar experiences, and we built a tool to help people navigate this more easily. It's called <strong>TurboNIW</strong>.

The goal is to provide a petition draft and completed forms, designed for researchers who want to take control of their NIW application but need a clearer roadmap and guidance through the process. We know how challenging this journey can be, and we wanted to create something that could help reduce the stress and uncertainty.

I'm not pushing this at all, just sharing in case it's useful to you, your students, or colleagues who are dealing with NIW. If you're a professor or industry researcher, feel free to pass it along to anyone who might benefit. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

As part of supporting the community, our website features the latest news and frequently asked questions about NIW immigration.

Always happy to chat about the NIW process or compare notes!

Best wishes with your research!

Best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_12 = """Hi {name},

I hope this message finds you well.

I recently came across your work titled "<em>{paper_title}</em>", and it stood out to me, particularly because it touches on areas that fall under the U.S. Critical and Emerging Technologies framework. For researchers in these fields, the National Interest Waiver (NIW) green card can be a practical pathway worth considering.

A bit about myself: I'm Wen, and I used to be an international PhD student. I went through the NIW application process on my own, and I remember how challenging it was. Many researchers face a difficult situation: attorney fees can be quite high, which makes it hard for many of us, while trying to DIY it felt like navigating a maze without a map, not knowing where to start or what the process should look like.

After going through that experience, I teamed up with a few others (former PhD students) to create a tool that could make this process more accessible. We built <strong>TurboNIW</strong>.

It's a straightforward DIY tool that generates petition drafts and completes forms. The idea is to give people a solid starting point and clear guidance, reducing the stress and uncertainty that comes with navigating the process alone. We built this because we understand how overwhelming this can feel, and we wanted to help others who might be in the same situation.

I'm sharing this purely as a resource. If it's not relevant to you personally, perhaps it's useful for students or colleagues navigating NIW. No pressure whatsoever. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

Our website also provides community resources, with the most recent news and Q&As about NIW immigration.

Feel free to reach out anytime if you want to discuss the NIW process or exchange experiences!

Best wishes with your research!

Best regards,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_13 = """Hi {name},

Hope you're doing well.

I recently read your paper "<em>{paper_title}</em>" and found it really interesting. Your work touches on areas that are part of the U.S. Critical and Emerging Technologies list, which made me think about how National Interest Waiver (NIW) green cards can be relevant for researchers in these fields.

I'm Wen, and I was an international PhD student who went through the NIW process. What I remember most is how stuck many of us feel. On one hand, hiring an attorney costs a lot, often more than what's realistic for early career researchers. On the other hand, trying to do it yourself feels impossible when you don't know where to begin, what forms you need, or what a strong application looks like.

That's what led a few of us (former international PhD students) to build <strong>TurboNIW</strong>.

It's a tool that creates petition letter drafts and fills out forms, designed for people who want to handle their NIW application themselves but need a clear starting point and some guidance. We made this because we know how stressful and uncertain this process can be, and we wanted to help others feel more confident navigating it.

I'm sharing this in case it's useful to you or anyone in your network who might be dealing with NIW. No pressure at all, just wanted to pass it along. We also really appreciate when people share it with others who might benefit, and we're always happy to show our appreciation for referrals.

We also keep our website updated with community resources, including the latest NIW immigration news and common questions.

Feel free to reach out if you want to talk about the NIW process or share experiences.

Best wishes with your research!

Best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_14 = """Hi {name},

I hope you're having a good week.

I came across your work "<em>{paper_title}</em>" and it caught my attention. Given the areas you're working in, I thought you might find it useful to know about NIW (National Interest Waiver) green cards, which can be a valuable option for researchers whose work aligns with critical technology areas.

Let me introduce myself: I'm Wen, a former international PhD student. When I was going through the NIW application, I realized how tough the situation is for many researchers. Attorney fees are often quite high, which makes it difficult for many of us, while the DIY approach feels overwhelming because there's no clear roadmap for beginners on where to start, what forms to complete, or how to structure everything.

After finishing my degree, I worked with a few others who had similar experiences, and together we created <strong>TurboNIW</strong>.

The idea is to provide petition drafts and completed forms, giving people a solid foundation if they want to handle NIW themselves. We built this because we understand how challenging and uncertain this journey can be, and we wanted to help others navigate it with more confidence and less stress.

I'm sharing this purely as a resource, in case it's helpful for you, your students, or colleagues who might be navigating NIW. Totally optional, just wanted to pass it along. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

Our website also offers community resources, with recent news and Q&As about NIW immigration.

Happy to chat more about NIW anytime!

Best wishes with your research!

Best regards,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


EMAIL_BODY_VARIANT_15 = """Hi {name},

Hope this message finds you well.

I wanted to reach out because I recently saw your work titled "<em>{paper_title}</em>". It's really impressive, and it reminded me of how many international researchers are working on technologies that fall under the U.S. government's Critical and Emerging Technologies framework, which can make National Interest Waiver (NIW) green card pathways quite relevant.

I'm Wen, and I used to be an international PhD student in the U.S. Going through the NIW process myself, I quickly learned how difficult it can be. Many of us face a challenging situation: attorney costs can be quite high, which isn't always feasible, while trying to do it yourself feels like you're lost without a guide, not knowing where to start or what the process should look like.

To help address this, a few of us who went through the same experience built a straightforward tool called <strong>TurboNIW</strong>.

It helps generate petition drafts and completed forms, designed for researchers who want to take control of their NIW application but need a clearer roadmap and guidance. We created this because we know how stressful and uncertain this process can be, and we wanted to help others feel more confident navigating it.

I'm not pushing this at all, just sharing in case it's useful to you, your students, or colleagues dealing with NIW. If you're a professor or work in industry, feel free to pass it along to anyone who might benefit. We also value peer recommendations, so if you know anyone who might benefit, we'd appreciate you sharing it with them, and we're always happy to show our appreciation for referrals.

We've also built our website as a community resource, featuring recent news and answers to common questions about NIW immigration.

Always happy to discuss the NIW process or compare notes!

Best wishes with your research!

All the best,
Wen

--
<strong>We've Been There. Now, We're Here for You.</strong>
<strong>TurboNIW</strong>

--
<em>Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC</em>
"""


# ============================================================================
# VARIANT SELECTION
# ============================================================================

def get_random_subject(publication_venue="arXiv"):
    """
    Returns a random subject line variant.
    
    Args:
        publication_venue: Not used anymore (kept for compatibility)
    
    Returns:
        A random subject line string
    """
    subject = random.choice(SUBJECT_VARIANTS)
    return subject  # No formatting needed, all subjects are complete


def get_random_email_body(name, paper_title="", publication_venue="arXiv"):
    """
    Returns a random email body variant with placeholders filled.
    
    Args:
        name: Recipient's full name (will extract first name)
        paper_title: Title of the paper
        publication_venue: Publication venue (used in subject line only)
    
    Returns:
        A formatted email body string
    """
    # Extract first name
    first_name = name.split()[0] if name and name.strip() else name
    
    # Choose random variant
    variants = [
        EMAIL_BODY_VARIANT_1,
        EMAIL_BODY_VARIANT_2,
        EMAIL_BODY_VARIANT_3,
        EMAIL_BODY_VARIANT_4,
        EMAIL_BODY_VARIANT_5,
        EMAIL_BODY_VARIANT_6,
        EMAIL_BODY_VARIANT_7,
        EMAIL_BODY_VARIANT_8,
        EMAIL_BODY_VARIANT_9,
        EMAIL_BODY_VARIANT_10,
        EMAIL_BODY_VARIANT_11,
        EMAIL_BODY_VARIANT_12,
        EMAIL_BODY_VARIANT_13,
        EMAIL_BODY_VARIANT_14,
        EMAIL_BODY_VARIANT_15,
    ]
    
    template = random.choice(variants)
    
    return template.format(
        name=first_name,
        paper_title=paper_title
    )


def format_email(name, paper_title="", publication_venue="arXiv"):
    """
    Generate a complete email with random subject and body.
    
    Args:
        name: Recipient's full name
        paper_title: Title of the paper
        publication_venue: Publication venue name (used in subject variant 3)
    
    Returns:
        Tuple of (subject, body)
    """
    subject = get_random_subject(publication_venue)
    body = get_random_email_body(name, paper_title, publication_venue)
    
    return subject, body


# ============================================================================
# LEGACY COMPATIBILITY (for existing code)
# ============================================================================

# For backward compatibility with old template system
EMAIL_TEMPLATE = EMAIL_BODY_VARIANT_1  # Default to variant 1

