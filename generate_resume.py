import fitz

doc = fitz.open()
page = doc.new_page()

text = """
John Doe
Software Engineer
Email: john.doe@example.com | Phone: (123) 456-7890 | LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

SUMMARY
Highly skilled and results-driven Software Engineer with 5+ years of experience in developing scalable web applications. Proficient in Python, Java, JavaScript, and cloud technologies. Strong background in microservices architecture and Agile methodologies.

SKILLS
- Languages: Python, Java, JavaScript (ES6+), SQL, HTML/CSS
- Frameworks/Libraries: Spring Boot, FastAPI, React.js, Node.js, Express
- Databases: PostgreSQL, MySQL, MongoDB, Redis
- Cloud/DevOps: AWS (EC2, S3, RDS), Docker, Kubernetes, CI/CD, Git

EXPERIENCE
Senior Software Engineer | Tech Solutions Inc. | San Francisco, CA | Jan 2021 - Present
- Architected and deployed scalable RESTful APIs using Spring Boot and Java, improving system response time by 40%.
- Led a team of 4 engineers to migrate legacy monolithic application to microservices architecture using Docker and Kubernetes.
- Optimized database queries in PostgreSQL, reducing average query execution time by 30%.
- Implemented CI/CD pipelines using GitHub Actions, enabling automated testing and daily deployments.

Software Engineer | Innovatech LLC | New York, NY | Jun 2018 - Dec 2020
- Developed responsive front-end interfaces using React.js and Redux for a SaaS product with over 10,000 active users.
- Built scalable backend services using Python and FastAPI, handling 500+ requests per second.
- Integrated third-party payment gateways (Stripe, PayPal) to process over $1M in monthly transactions.
- Collaborated closely with product managers and designers in Agile sprints.

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley | May 2018
GPA: 3.8/4.0

PROJECTS
E-Commerce Platform (Personal Project)
- Developed a full-stack e-commerce application using MERN stack (MongoDB, Express, React, Node.js).
- Implemented JWT authentication and integrated Stripe API for secure payments.

AI Resume Analyzer
- Built an AI-powered resume analyzer using FastAPI, React, and NLP techniques to match resumes with job descriptions.
"""

rect = fitz.Rect(50, 50, 550, 800)
page.insert_textbox(rect, text.strip(), fontsize=10, fontname="helv")

doc.save("Sample_Software_Engineer_Resume.pdf")
print("PDF created successfully at Sample_Software_Engineer_Resume.pdf")
