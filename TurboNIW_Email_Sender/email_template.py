"""
Email template for TurboNIW outreach.
Contains the email template with placeholders that can be replaced.
"""

EMAIL_TEMPLATE = """Hi {name},

I hope you're doing well.

I recently came across your work published in {publication_venue}. The research is genuinely interesting, and it aligns with several areas included in the White House's Critical and Emerging Technologies list. For researchers whose work falls into these categories, the NIW (National Interest Waiver) green card can be an important option, especially for those who may consider coming to the U.S. in the future.

I'm Wen. I used to be an international Ph.D. student, and I'm now an entrepreneur working on tools to help early-career researchers navigate U.S. immigration pathways more easily.

As someone who went through this process myself during my PhD, I remember two big challenges: attorney fees are extremely high (usually $8,000–$10,000+), and the DIY route can be overwhelming because beginners don't know where to start, what forms to fill out, how to structure the letter, or what the materials should look like.

Because of that, a few of us (all former U.S. PhD students) built a simple, affordable tool to help others navigate the first steps. It's called TurboNIW:

https://www.turboniw.com/

It provides a quick petition draft and completed forms at a cost closer to half a month of a PhD stipend, rather than the several thousand dollars charged by attorneys. It's meant to reduce the time, uncertainty, and stress for people who want to handle NIW themselves.

I'm sharing this purely in case it's helpful (not as a push). If you're a professor or a researcher in industry and don't need this yourself, I'd appreciate it if you could pass it along to any international students or colleagues who might be navigating NIW or need a fast start.

Feel free to reach out anytime if you want to chat about the NIW process or compare experiences.

Best,
Wen

We've Been There. Now, We're Here for You.

--
Wen Xie, Faculty Postdoc Fellow at Experiential AI
Northeastern University
Personal Website: https://wenxie18.github.io/
LinkedIn: https://www.linkedin.com/in/vincexie/
Ph.D., Electrical Engineering, University of Houston
B.ENG. Electronic Information Engineering, UESTC
B.A. Finance, UESTC
"""


def format_email(name, paper_title=None, publication_venue="ACL"):
    """
    Format the email template with provided values.
    
    Args:
        name: Recipient's full name (will extract first name)
        paper_title: Title of the paper (not used in template, kept for backward compatibility)
        publication_venue: Publication venue (conference/journal name)
    
    Returns:
        Formatted email string with placeholders replaced
    """
    # Extract first name by splitting on space and taking the first part
    first_name = name.split()[0] if name and name.strip() else name
    
    return EMAIL_TEMPLATE.format(
        name=first_name,
        publication_venue=publication_venue
    )

