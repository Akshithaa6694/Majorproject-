import streamlit as st
import re


def get_local_response(prompt):
    """
    Enhanced rule-based responses for any general question.
    Works without external API or internet connection.
    """
    prompt_lower = prompt.lower()
    
    # Try to match with partial keyword matching
    def find_best_match(text, keywords):
        """Find the best matching keyword in the text"""
        for keyword in keywords:
            if keyword in text or text in keyword:
                return keyword
        return None
    
    # Project-specific responses (only for explicit project questions)
    project_responses = {
        "this project": [
            "This is a Financial Fraud Detection project using machine learning. It uses a Random Forest model trained on synthetic transaction data to detect potentially fraudulent transactions.",
            "The project includes: real-time transaction analysis, risk scoring, explainable AI, and a dashboard interface for demo purposes."
        ],
        "your project": [
            "This is a Financial Fraud Detection project using machine learning. It uses a Random Forest model trained on synthetic transaction data to detect potentially fraudulent transactions.",
            "The project includes: real-time transaction analysis, risk scoring, explainable AI, and a dashboard interface for demo purposes."
        ],
        "the project": [
            "This is a Financial Fraud Detection project using machine learning. It uses a Random Forest model trained on synthetic transaction data to detect potentially fraudulent transactions.",
            "The project includes: real-time transaction analysis, risk scoring, explainable AI, and a dashboard interface for demo purposes."
        ],
        "this system": [
            "This fraud detection system uses a Random Forest machine learning model trained on synthetic transaction data.",
            "The model analyzes multiple risk factors: transaction amount, location, device, time, payment method, and channel.",
            "Common fraud indicators: high amounts (>₹20,000), international transactions, new devices, unusual times (late night/early morning), and distant locations."
        ],
        "the system": [
            "This fraud detection system uses a Random Forest machine learning model trained on synthetic transaction data.",
            "The model analyzes multiple risk factors: transaction amount, location, device, time, payment method, and channel.",
            "Common fraud indicators: high amounts (>₹20,000), international transactions, new devices, unusual times (late night/early morning), and distant locations."
        ],
        "implementation": [
            "This project uses a Random Forest classifier with 260 trees, max depth 13, trained on 7,000 synthetic transactions.",
            "Features include: amount, hour, city, country, merchant, payment method, device, channel, international flag, new device flag, and distance.",
            "The model achieves good performance on the synthetic demo dataset for educational purposes."
        ],
        "risk score": [
            "Risk scores in this system range from 0-99% based on ML predictions and rule-based signals.",
            "70%+ = FRAUD ALERT (red), 40-69% = REVIEW REQUIRED (yellow), <40% = LOW RISK (green).",
            "The score combines model probability (70% weight) with rule-based signals (30% weight)."
        ],
        "how to use": [
            "To analyze a transaction, go to the Transactions page and enter the details: amount, location, merchant, payment method, device, channel, and distance.",
            "The system provides real-time risk analysis with explainable reasons.",
            "You can also simulate incoming transactions for live demonstrations."
        ],
        "demo": [
            "This is a college demo project for educational purposes using synthetic transaction data.",
            "The login accepts any non-empty username and password for demo purposes.",
            "All data is stored locally in SQLite and is not connected to any real financial system."
        ]
    }
    
    # General knowledge responses - expanded for all topics
    general_responses = {
        "fraud": [
            "Fraud is intentional deception to secure unfair or unlawful gain, or to deprive a victim of a legal right. Types include financial fraud, identity theft, insurance fraud, and online scams.",
            "Fraud detection uses various methods: rule-based systems, machine learning, anomaly detection, and human investigation. Common red flags: unusual transactions, location changes, and new devices."
        ],
        "risk": [
            "Risk is the possibility of loss, injury, or other adverse circumstances. In finance, risk refers to the potential for financial loss or uncertainty in returns.",
            "Risk management involves identifying, assessing, and prioritizing risks followed by coordinated application of resources to minimize the impact of unfortunate events."
        ],
        "model": [
            "A model is a representation of reality used to understand, explain, or predict phenomena. In data science, models are mathematical representations trained on data to make predictions.",
            "Types of models: statistical models, machine learning models, physical models, and conceptual models. Models simplify complex systems to make them easier to understand and analyze."
        ],
        "transaction": [
            "A transaction is an exchange or transfer of goods, services, or funds. In finance, it refers to any activity that changes the financial position of an account.",
            "Transactions can be: debit/credit card payments, bank transfers, cash withdrawals, online purchases, and more. Each transaction has a timestamp, amount, and parties involved."
        ],
        "hello": ["Hello! How can I help you today?", "Hi there! What would you like to know?", "Hey! I'm here to help with any questions."],
        "hi": ["Hello! How can I assist you?", "Hi! What can I help you with?"],
        "name": ["I am FraudGuard AI, your helpful assistant. I can answer questions about this project and general topics.", "My name is FraudGuard AI, and I'm here to help you with any questions!"],
        "who are you": ["I am FraudGuard AI, an AI assistant that can answer questions about fraud detection and general topics without needing an internet connection."],
        
        # Programming & Technology
        "python": ["Python is a popular programming language known for its simplicity and readability. It's widely used in data science, machine learning, web development, and automation.", "Python's key features: easy syntax, extensive libraries (pandas, numpy, scikit-learn), cross-platform support, and large community."],
        "java": ["Java is a popular, object-oriented programming language known for its 'write once, run anywhere' capability. It's used in enterprise applications, Android development, and big data.", "Java features: platform independence, strong memory management, multithreading, and extensive libraries."],
        "javascript": ["JavaScript is the primary language for web development, used for both frontend and backend development. It powers interactive websites and web applications.", "JavaScript runs in browsers and can be used with frameworks like React, Vue, and Angular for frontend, and Node.js for backend."],
        "programming": ["Programming is the process of creating instructions for computers to execute tasks using programming languages. Popular languages include Python, Java, JavaScript, C++, and Go.", "To learn programming: start with basics, practice regularly, build projects, and learn from online resources like freeCodeCamp and Codecademy."],
        "coding": ["Coding is writing instructions in programming languages to create software applications. Best practices: write clean code, use version control (Git), add comments, and test your code.", "Resources for learning: freeCodeCamp, Codecademy, LeetCode, GitHub, and Stack Overflow."],
        "computer": ["A computer is an electronic device that processes data according to instructions. Components: CPU (processing), RAM (memory), Storage (hard drive/SSD), GPU (graphics), and Motherboard.", "Computers run operating systems like Windows, macOS, Linux, and mobile OS like Android and iOS."],
        "internet": ["The Internet is a global network of computers connected through communication protocols. It enables web browsing, email, online services, social media, and cloud computing.", "Key technologies: TCP/IP, HTTP, DNS, and WiFi. The Internet has revolutionized communication, business, and information access."],
        "software": ["Software is a set of instructions that tells a computer what to do. Types: system software (OS, drivers) and application software (browsers, games, productivity tools).", "Software development involves coding, testing, debugging, and maintaining programs. Popular development methodologies include Agile and DevOps."],
        "app": ["An app (application) is software designed for end-users. Types: mobile apps (Android, iOS), web apps (run in browsers), and desktop apps (Windows, Mac, Linux).", "Popular apps: WhatsApp, Instagram, Spotify, Microsoft Office, and countless others that help us work, communicate, and entertain ourselves."],
        "website": ["A website is a collection of web pages accessed through the internet. Websites are built using HTML, CSS, and JavaScript, and hosted on web servers.", "Types of websites: informational, e-commerce, social media, blogs, and web applications. Popular website builders include WordPress, Wix, and Squarespace."],
        "database": ["Databases store and organize data for applications. Types: Relational (SQL) and NoSQL. SQL databases: MySQL, PostgreSQL, SQLite. NoSQL: MongoDB, Redis, Cassandra.", "This project uses SQLite for storing transaction history. Databases are essential for any application that needs to store and retrieve data."],
        "sql": ["SQL (Structured Query Language) is used to manage and query relational databases. Common commands: SELECT (retrieve data), INSERT (add data), UPDATE (modify data), DELETE (remove data).", "SQL is essential for backend development, data analysis, and managing data in applications."],
        "api": ["API (Application Programming Interface) allows different software applications to communicate with each other. Types: REST, GraphQL, SOAP, and WebSocket.", "APIs are essential for integrating services, accessing data from third-party services, and building modular applications."],
        "cloud": ["Cloud computing provides on-demand computing resources over the internet. Types: IaaS (Infrastructure), PaaS (Platform), SaaS (Software).", "Popular providers: AWS, Google Cloud, Microsoft Azure, and DigitalOcean. Cloud computing enables scalable, flexible, and cost-effective IT solutions."],
        "cybersecurity": ["Cybersecurity protects computer systems and networks from digital attacks and unauthorized access. Key areas: network security, application security, information security, and disaster recovery.", "Best practices: strong passwords, two-factor authentication, regular updates, security awareness, and using antivirus software."],
        "hacking": ["Hacking refers to exploiting computer systems for unauthorized access. Ethical hacking (white-hat) helps identify security vulnerabilities. Malicious hacking (black-hat) is illegal.", "Security measures: firewalls, encryption, secure coding practices, regular security audits, and staying informed about threats."],
        "blockchain": ["Blockchain is a decentralized, distributed ledger technology that records transactions across multiple computers. Key features: immutability, transparency, and security through cryptography.", "Applications: cryptocurrencies (Bitcoin, Ethereum), smart contracts, supply chain tracking, and digital identity verification."],
        "cryptocurrency": ["Cryptocurrency is a digital or virtual currency that uses cryptography for security and operates on decentralized networks. Popular: Bitcoin, Ethereum, Ripple, and Litecoin.", "Cryptocurrencies can be volatile and are subject to regulatory scrutiny. They offer potential for decentralized finance and borderless transactions."],
        "bitcoin": ["Bitcoin is the first and most well-known cryptocurrency, created in 2009 by an anonymous person or group known as Satoshi Nakamoto. It operates on a decentralized blockchain network.", "Bitcoin features: limited supply (21 million coins), peer-to-peer transactions, and no central authority. It's often called 'digital gold'."],
        "ai": ["Artificial Intelligence (AI) is the simulation of human intelligence in machines. It includes machine learning, natural language processing, computer vision, and robotics.", "AI applications: virtual assistants (Siri, Alexa), image recognition, language translation, autonomous vehicles, recommendation systems, and fraud detection."],
        "machine learning": ["Machine Learning (ML) is a subset of AI where computers learn from data to make predictions or decisions without being explicitly programmed.", "Common ML types: Supervised learning (classification, regression), Unsupervised learning (clustering), and Reinforcement learning. Popular algorithms: Random Forest, Neural Networks, SVM."],
        "data science": ["Data Science combines statistics, programming, and domain knowledge to extract insights from data. Key skills: Python/R programming, SQL, statistics, machine learning, and data visualization.", "Tools: pandas, numpy, scikit-learn, TensorFlow, PyTorch, Tableau, and Apache Spark. Data scientists help organizations make data-driven decisions."],
        "algorithm": ["An algorithm is a step-by-step procedure for solving a problem or completing a task. Common algorithms: sorting (quick sort, merge sort), searching (binary search), and graph algorithms (Dijkstra, BFS, DFS).", "Understanding algorithms is crucial for efficient programming and problem-solving. Good algorithms can significantly improve application performance."],
        "git": ["Git is a version control system for tracking changes in code and collaborating with others. Common commands: git init, git add, git commit, git push, git pull, git branch.", "Git is essential for software development teams and open-source projects. It helps manage code history, collaborate with others, and revert changes if needed."],
        "github": ["GitHub is a web-based platform for hosting Git repositories and collaborating on code. Features: version control, issue tracking, pull requests, and CI/CD integration.", "GitHub is widely used for open-source projects and team collaboration. It's the world's largest platform for software development."],
        
        # Science
        "science": ["Science is the systematic study of the natural world through observation and experimentation. Main branches: Physics, Chemistry, Biology, Earth Science, and Astronomy.", "The scientific method involves observation, hypothesis, experimentation, analysis, and conclusion. Science has led to countless technological advancements."],
        "physics": ["Physics is the study of matter, energy, and the fundamental forces of nature. Key areas: mechanics, thermodynamics, electromagnetism, optics, and quantum mechanics.", "Famous physicists: Newton, Einstein, Feynman, Curie. Physics explains how the universe works, from subatomic particles to galaxies."],
        "chemistry": ["Chemistry is the study of matter, its properties, composition, and reactions. Branches: organic, inorganic, physical, analytical, and biochemistry.", "Chemistry is central to understanding materials, medicines, environmental processes, and biological systems. It's essential for pharmaceuticals, materials science, and industry."],
        "biology": ["Biology is the study of living organisms and their interactions. Branches: molecular biology, genetics, ecology, evolution, and physiology.", "Biology helps us understand life processes, diseases, ecosystems, and biodiversity. It's crucial for medicine, conservation, and biotechnology."],
        "math": ["Mathematics is the study of numbers, quantities, shapes, and patterns. Key areas: algebra, calculus, statistics, geometry, and discrete mathematics.", "Math is fundamental to science, engineering, finance, and technology. It's the language of the universe and essential for problem-solving."],
        "chemistry": ["Chemistry is the scientific study of the properties and behavior of matter. It deals with the composition of substances, their reactions, and the formation of new compounds.", "Chemistry is essential for understanding materials, medicines, environmental processes, and biological systems. Applications include pharmaceuticals, materials science, and industrial processes."],
        "biology": ["Biology is the study of living organisms, including their structure, function, growth, origin, evolution, and distribution. Major branches: molecular biology, genetics, ecology, and physiology.", "Biology is crucial for understanding life, diseases, ecosystems, and developing medicines, vaccines, and biotechnology solutions."],
        "evolution": ["Evolution is the process by which species change over time through natural selection and genetic variation. Proposed by Charles Darwin in his theory of evolution by natural selection.", "Evolution explains the diversity of life on Earth and how species adapt to their environments. Evidence includes fossils, genetics, and comparative anatomy."],
        "dna": ["DNA (Deoxyribonucleic Acid) is the molecule that carries genetic instructions for life. It has a double helix structure and contains genes that determine traits.", "DNA is found in all living organisms and determines characteristics like eye color, height, and susceptibility to diseases. DNA testing is used in forensics, medicine, and ancestry."],
        "atom": ["An atom is the smallest unit of ordinary matter that defines a chemical element. It consists of a nucleus (protons and neutrons) surrounded by electrons.", "Atoms combine to form molecules and compounds. Different elements have different numbers of protons, which determine their chemical properties."],
        "energy": ["Energy is the capacity to do work. Forms: kinetic (motion), potential (stored), thermal (heat), chemical, electrical, and nuclear. Energy can be converted between forms but never created or destroyed.", "Energy is essential for all processes. Sources include fossil fuels, renewable energy (solar, wind, hydro), and nuclear. Conservation of energy is a fundamental physics principle."],
        "gravity": ["Gravity is the force that attracts objects with mass toward each other. On Earth, it gives weight to objects and causes them to fall. Described by Newton's law of universal gravitation and Einstein's theory of general relativity.", "Gravity keeps planets in orbit, causes tides, and shapes the structure of the universe. Understanding gravity is crucial for space exploration and engineering."],
        
        # History
        "history": ["History is the study of past events, particularly human affairs. It helps us understand the present and future by learning from the past.", "Key periods: Ancient (Egypt, Greece, Rome), Medieval, Renaissance, Industrial Revolution, World Wars, and Modern era. History provides context for current events and cultural understanding."],
        "ancient": ["Ancient history covers early civilizations like Mesopotamia, Egypt, Greece, Rome, China, and India. These civilizations developed writing, agriculture, architecture, and governance.", "Ancient contributions: democracy (Greece), law codes (Hammurabi), philosophy (Socrates, Plato), engineering (Roman), and mathematics (Egypt, India)."],
        "war": ["Wars have shaped human history significantly. Major conflicts: World War I (1914-1918), World War II (1939-1945), and numerous regional conflicts throughout history.", "Wars have consequences: loss of life, political changes, technological advances, and social transformations. Understanding wars helps prevent future conflicts."],
        "revolution": ["Revolutions are fundamental changes in political power or organizational structures. Examples: American Revolution (1776), French Revolution (1789), Industrial Revolution (18th-19th century).", "Revolutions can be political, social, technological, or industrial. They often bring significant changes to society, governance, and economy."],
        "industrial": ["The Industrial Revolution (18th-19th century) transformed society from agrarian to industrial. Key innovations: steam engine, textile manufacturing, iron production, and later electricity.", "The Industrial Revolution led to urbanization, mass production, economic growth, and social changes. It marked the beginning of modern industrial society."],
        
        # Geography
        "geography": ["Geography is the study of places, relationships between people and their environments, and the Earth's physical features. Branches: physical geography (landforms, climate) and human geography (population, culture).", "Geography helps us understand the world, its diversity, and human-environment interactions. It's essential for planning, conservation, and global awareness."],
        "country": ["There are 195 recognized countries in the world. Each has unique culture, geography, economy, and political system. Countries interact through trade, diplomacy, and international organizations.", "Learning about countries helps understand global diversity, international relations, and cultural differences. Popular to learn: capitals, languages, and famous landmarks."],
        "india": ["India is a South Asian country with a population of over 1.4 billion. It's known for its diverse culture, rich history, ancient civilizations, and rapid economic growth.", "India's capital is New Delhi. Major cities: Mumbai, Bangalore, Chennai, Hyderabad. India is the world's largest democracy and has a thriving IT industry."],
        "usa": ["The United States is a North American country with 50 states. It's known for its cultural influence, technological innovation, and economic power. Capital: Washington D.C.", "The USA has diverse geography, from coastlines to mountains. It's a leader in technology, entertainment, and higher education. Major cities: New York, Los Angeles, Chicago."],
        "china": ["China is an East Asian country with the world's largest population (over 1.4 billion). It's known for its rapid economic growth, ancient civilization, and technological advancement. Capital: Beijing.", "China has a rich history spanning thousands of years. It's a major global economic power and the world's manufacturing hub. Major cities: Shanghai, Guangzhou, Shenzhen."],
        "europe": ["Europe is a continent with 44 countries. Known for its rich history, diverse cultures, art, architecture, and political integration through the European Union.", "European countries: France, Germany, Italy, Spain, UK, and many more. Europe has been central to world history, from ancient Greece and Rome to modern times."],
        "africa": ["Africa is the world's second-largest continent with 54 countries. Known for its diverse cultures, wildlife, natural resources, and rich history. It's the cradle of humanity.", "Africa has diverse ecosystems: deserts (Sahara), rainforests (Congo), savannas (Serengeti). It's home to incredible wildlife and ancient civilizations like Egypt."],
        "ocean": ["Oceans cover about 71% of Earth's surface. Five oceans: Pacific (largest), Atlantic, Indian, Southern, and Arctic. They regulate climate, support marine life, and enable global trade.", "Oceans are crucial for life on Earth. They provide food, oxygen, regulate climate, and are home to diverse marine ecosystems. Concerns: pollution, overfishing, and climate change."],
        "mountain": ["Mountains are elevated landforms with steep sides. Famous mountains: Mount Everest (highest), K2, Kilimanjaro, and the Rocky Mountains.", "Mountains are important for water sources, biodiversity, and recreation. They're formed by tectonic plate movement and volcanic activity. Mountain ranges: Himalayas, Alps, Andes."],
        "river": ["Rivers are natural flowing watercourses. Major rivers: Nile (longest), Amazon (largest by volume), Mississippi, Yangtze, and Ganges.", "Rivers are vital for freshwater, agriculture, transportation, and ecosystems. They've been central to human civilization throughout history."],
        
        # Literature & Arts
        "book": ["Books are written or printed works consisting of pages bound together. Genres: fiction, non-fiction, poetry, drama, and more. Books preserve knowledge, tell stories, and educate.", "Reading books improves vocabulary, concentration, and empathy. Famous authors: Shakespeare, Tolstoy, Austen, Dickens, and contemporary writers across all genres."],
        "poetry": ["Poetry is a form of literature that uses aesthetic and rhythmic qualities of language. Types: sonnets, haiku, free verse, and epic poetry. Famous poets: Shakespeare, Wordsworth, Tagore, Rumi.", "Poetry expresses emotions, tells stories, and explores ideas in condensed, artistic form. It's been part of human culture for thousands of years."],
        "art": ["Art is creative expression through various mediums: painting, sculpture, music, dance, literature, and more. Art reflects culture, emotions, and ideas.", "Art movements: Renaissance, Impressionism, Modernism, and Contemporary. Famous artists: Da Vinci, Van Gogh, Picasso, and countless others who shaped visual culture."],
        "music": ["Music is an art form combining sounds, rhythm, and melody. Genres: classical, pop, rock, jazz, hip-hop, electronic, and traditional music from around the world.", "Music has universal appeal and can evoke emotions, tell stories, and bring people together. Instruments: piano, guitar, violin, drums, and many more."],
        "movie": ["Movies (films) are motion pictures that tell stories through visual and audio elements. Genres: drama, comedy, action, horror, sci-fi, and documentary.", "Cinema is a powerful medium for storytelling and cultural expression. Famous films influence culture, inspire audiences, and reflect societal values and issues."],
        "literature": ["Literature is written works considered to have artistic merit. Includes novels, poetry, plays, essays, and more. It reflects human experience and culture.", "Literature helps us understand different perspectives, times, and places. Classic literature: Shakespeare, Homer, Dante, and works from all cultures and eras."],
        
        # Sports
        "sport": ["Sports are physical activities involving competition. Popular sports: football (soccer), cricket, basketball, tennis, athletics, swimming, and many more.", "Sports promote physical fitness, teamwork, discipline, and sportsmanship. Major events: Olympics, World Cup, and various championships that bring global attention."],
        "football": ["Football (soccer) is the world's most popular sport, played by two teams of 11 players. The objective is to score goals by getting the ball into the opposing team's net.", "FIFA World Cup is the most-watched sporting event globally. Famous players: Messi, Ronaldo, Pelé, Maradona. Football promotes teamwork and passion."],
        "cricket": ["Cricket is a bat-and-ball game played between two teams of 11 players. Popular in countries like India, Australia, England, Pakistan, and South Africa.", "Formats: Test (5 days), One Day (50 overs), and T20 (20 overs). Cricket requires strategy, skill, and teamwork. World Cup is a major international tournament."],
        "basketball": ["Basketball is a team sport where two teams of five players try to score by shooting a ball through a hoop. Popular in the USA and globally.", "NBA is the premier basketball league. Famous players: Michael Jordan, LeBron James, Kobe Bryant. Basketball emphasizes athleticism, teamwork, and skill."],
        "tennis": ["Tennis is a racket sport played individually or in pairs. Players hit a ball over a net using rackets. Grand Slam tournaments: Wimbledon, US Open, French Open, Australian Open.", "Tennis requires skill, agility, and strategy. Famous players: Federer, Nadal, Djokovic, Serena Williams. It's popular both as a spectator sport and recreational activity."],
        "olympics": ["The Olympics is a major international multi-sport event. Summer and Winter Olympics feature athletes from around the world competing in various sports.", "The Olympics promote international unity, peace, and excellence in sports. It originated in ancient Greece and was revived in 1896. Host cities showcase their culture and facilities."],
        
        # Food & Cooking
        "food": ["Food is any substance consumed to provide nutritional support. Cuisines vary by region: Indian, Italian, Chinese, Mexican, French, and many more.", "Food is central to culture, health, and social gatherings. A balanced diet includes proteins, carbohydrates, fats, vitamins, and minerals."],
        "cooking": ["Cooking is the art and science of preparing food using heat, ingredients, and techniques. Methods: baking, frying, grilling, boiling, steaming, and more.", "Cooking skills can be learned and improved with practice. It's a creative activity that brings people together and allows cultural expression through food."],
        "recipe": ["A recipe is a set of instructions for preparing a dish. It includes ingredients, quantities, and step-by-step cooking methods.", "Recipes can be traditional family favorites or innovative creations. They preserve culinary traditions and allow sharing of delicious dishes."],
        "health": ["Health is a state of physical, mental, and social well-being. Maintaining good health involves: regular exercise, balanced diet, adequate sleep, stress management, and regular check-ups.", "Mental health is equally important: practice mindfulness, seek support when needed, and maintain social connections. Preventive care includes vaccinations and healthy lifestyle choices."],
        "nutrition": ["Nutrition is the study of nutrients in food and how the body uses them. Key nutrients: proteins, carbohydrates, fats, vitamins, minerals, and water.", "Good nutrition is essential for growth, energy, disease prevention, and overall well-being. Different life stages require different nutritional needs."],
        "exercise": ["Exercise is physical activity that enhances or maintains physical fitness. Types: aerobic (running, swimming), strength training, flexibility (yoga), and balance exercises.", "Regular exercise improves cardiovascular health, muscle strength, mental health, and overall quality of life. Recommended: at least 150 minutes of moderate activity per week."],
        
        # Society & Culture
        "culture": ["Culture encompasses the beliefs, customs, arts, and social behavior of a particular society or group. It includes language, religion, cuisine, music, art, and traditions.", "Culture shapes identity, values, and social interactions. Understanding different cultures promotes tolerance, empathy, and global citizenship."],
        "religion": ["Religion is a system of beliefs and practices concerning the divine or sacred. Major religions: Christianity, Islam, Hinduism, Buddhism, Judaism, and others.", "Religion influences culture, ethics, values, and social structures. It provides meaning, community, and moral guidance for billions of people worldwide."],
        "society": ["Society is the aggregate of people living together in a community. It involves social structures, institutions, relationships, and cultural norms.", "Societies evolve over time and vary across regions. Understanding society helps navigate social interactions, address social issues, and build better communities."],
        "politics": ["Politics is the activities associated with governance and decision-making in a group or society. It involves elections, policy-making, and power dynamics.", "Political systems: democracy, monarchy, dictatorship, and republic. Understanding politics is important for civic engagement and understanding how societies are governed."],
        "economy": ["Economy is the system of production, distribution, and consumption of goods and services. Types: capitalist, socialist, mixed economies.", "Economic indicators: GDP, inflation, unemployment, and trade balance. Understanding economics helps in personal finance, business decisions, and policy understanding."],
        "money": ["Money is a medium of exchange, store of value, and unit of account. Forms: cash, bank deposits, digital currencies. It facilitates trade and economic activity.", "Personal finance: budgeting, saving, investing, and managing debt. Financial literacy is important for making informed money decisions and achieving financial goals."],
        "business": ["Business is an organization or enterprising entity engaged in commercial, industrial, or professional activities. Types: sole proprietorship, partnership, corporation.", "Business involves producing goods or services, creating value, and generating profit. Key aspects: marketing, finance, operations, and human resources."],
        "education": ["Education is the process of learning and acquiring knowledge, skills, values, and beliefs. Types: formal (schools, universities), informal (self-learning, online courses), and non-formal (workshops, training).", "Education is essential for personal development, career opportunities, and societal progress. Lifelong learning is important in today's rapidly changing world."],
        "career": ["Building a successful career involves: continuous learning, networking, setting goals, and adapting to change. Popular careers: technology, healthcare, finance, education, and creative fields.", "Key career skills: problem-solving, communication, teamwork, technical expertise, and adaptability. Career planning helps achieve professional goals and satisfaction."],
        "job": ["A job is a regular activity performed in exchange for payment. Jobs vary by industry, skill level, and responsibilities. Finding the right job involves skills, networking, and persistence.", "Job market trends shift with technology and economy. Continuous learning and skill development are important for career advancement and job security."],
        
        # Psychology & Philosophy
        "psychology": ["Psychology is the scientific study of the mind and behavior. Areas: cognitive, developmental, social, clinical, and industrial-organizational psychology.", "Psychology helps understand mental processes, emotions, relationships, and mental health. Applications: therapy, education, workplace, and personal development."],
        "philosophy": ["Philosophy is the study of fundamental questions about existence, knowledge, values, reason, mind, and language. Branches: ethics, metaphysics, epistemology, and logic.", "Philosophy develops critical thinking, ethical reasoning, and understanding of life's big questions. Famous philosophers: Socrates, Plato, Aristotle, Kant, Nietzsche."],
        "mind": ["The mind refers to the cognitive and conscious aspects of consciousness, including thoughts, perceptions, memories, and emotions. It's studied in psychology, neuroscience, and philosophy.", "Understanding the mind is important for mental health, decision-making, and self-awareness. Practices like meditation and mindfulness can improve mental well-being."],
        "emotion": ["Emotions are psychological states that involve feelings, physiological changes, and behavioral responses. Common emotions: happiness, sadness, anger, fear, surprise, and disgust.", "Emotions are essential for human experience, decision-making, and social communication. Emotional intelligence involves recognizing and managing emotions effectively."],
        "happiness": ["Happiness is a positive emotional state characterized by feelings of joy, satisfaction, and contentment. Factors: relationships, health, purpose, and mindset.", "Practices for happiness: gratitude, positive relationships, meaningful activities, healthy lifestyle, and helping others. Happiness is both a feeling and a life satisfaction measure."],
        "stress": ["Stress is the body's response to pressure or challenges. It can be acute (short-term) or chronic (long-term). Too much stress can harm health and well-being.", "Stress management: exercise, meditation, deep breathing, time management, social support, and seeking professional help if needed. Balance and self-care are important."],
        
        # Environment
        "environment": ["The environment includes all living and non-living things around us. It encompasses air, water, land, ecosystems, and climate. Environmental protection is crucial for sustainability.", "Environmental issues: climate change, pollution, deforestation, biodiversity loss, and resource depletion. Conservation efforts aim to protect ecosystems for future generations."],
        "climate": ["Climate is the long-term pattern of weather conditions in a region. Climate change refers to significant changes in global weather patterns, largely due to human activities like burning fossil fuels.", "Climate change impacts: rising temperatures, extreme weather, sea-level rise, and ecosystem disruption. Mitigation: reducing emissions, renewable energy, and conservation."],
        "weather": ["Weather refers to the state of the atmosphere at a specific time and place. It includes temperature, humidity, wind, precipitation, and atmospheric pressure.", "Weather forecasting uses satellites, radar, and computer models to predict conditions. Weather affects daily life, agriculture, transportation, and safety."],
        "nature": ["Nature encompasses the natural world, including plants, animals, landscapes, and ecosystems. It provides resources, beauty, and ecological balance.", "Connecting with nature has mental health benefits. Conservation efforts protect biodiversity and natural habitats. Sustainable living helps preserve nature for future generations."],
        "pollution": ["Pollution is the introduction of harmful substances into the environment. Types: air pollution, water pollution, soil pollution, and noise pollution.", "Pollution harms health, ecosystems, and quality of life. Solutions: cleaner technologies, regulations, recycling, and individual actions to reduce waste and emissions."],
        "recycling": ["Recycling is processing used materials into new products. It reduces waste, conserves resources, and reduces pollution. Common recyclables: paper, plastic, glass, and metal.", "Recycling is part of sustainable living. It helps reduce landfill waste, conserve natural resources, and decrease environmental impact. Sorting and proper disposal are important."],
        
        # Space & Universe
        "space": ["Space is the vast expanse beyond Earth's atmosphere. It contains stars, planets, galaxies, and other celestial objects. Space exploration has advanced our understanding of the universe.", "Space missions: Moon landing, Mars rovers, space stations (ISS), and telescopes (Hubble, James Webb). Space research benefits technology, communication, and Earth observation."],
        "universe": ["The universe is all of space and time, including all matter and energy. It's estimated to be 13.8 billion years old and contains billions of galaxies.", "The universe is expanding. Key questions: dark matter, dark energy, and whether life exists elsewhere. Space exploration continues to reveal its mysteries."],
        "star": ["Stars are massive celestial bodies that produce light and heat through nuclear fusion. Our Sun is a star. Stars vary in size, temperature, and lifespan.", "Stars form in nebulae (gas and dust clouds) and end as white dwarfs, neutron stars, or black holes. They're essential for the formation of planetary systems and the elements of life."],
        "planet": ["Planets are celestial bodies orbiting stars. Our solar system has 8 planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.", "Planets vary in size, composition, and conditions. Exoplanets (planets outside our solar system) are being discovered, some potentially habitable."],
        "moon": ["The Moon is Earth's only natural satellite. It affects tides, stabilizes Earth's rotation, and has been the target of human space exploration.", "Moon phases: new moon, crescent, quarter, gibbous, and full moon. The Moon has been visited by astronauts and studied extensively by space missions."],
        "galaxy": ["A galaxy is a massive system of stars, gas, dust, and dark matter bound by gravity. Our galaxy is the Milky Way. Galaxies come in various shapes: spiral, elliptical, and irregular.", "The universe contains billions of galaxies. Galaxy formation and evolution are key areas of cosmology. Studying galaxies helps understand the universe's structure and history."],
        
        # Entertainment
        "game": ["Games are structured activities for entertainment, competition, or learning. Types: video games, board games, sports, and puzzles. Games can be solo or multiplayer.", "Gaming is a popular form of entertainment and can develop skills like strategy, problem-solving, and teamwork. The gaming industry is a major global entertainment sector."],
        "movie": ["Movies (films) are motion pictures that tell stories through visual and audio elements. Genres: drama, comedy, action, horror, sci-fi, and documentary.", "Cinema is a powerful medium for storytelling and cultural expression. Films can entertain, educate, inspire, and provoke thought about important issues."],
        "music": ["Music is an art form combining sounds, rhythm, and melody. Genres: classical, pop, rock, jazz, hip-hop, electronic, and traditional music from around the world.", "Music has universal appeal and can evoke emotions, tell stories, and bring people together. It's an integral part of human culture and expression."],
        "television": ["Television is a medium for transmitting moving images and sound. It provides news, entertainment, education, and cultural content.", "TV has evolved from broadcast to streaming services. It's a major source of entertainment and information, shaping culture and public discourse."],
        
        # Misc
        "love": ["Love is a complex set of emotions, behaviors, and beliefs associated with strong feelings of affection, protectiveness, warmth, and respect for another person or thing.", "Types of love: romantic love, familial love, platonic love, and self-love. Love is fundamental to human relationships and well-being, fostering connection and happiness."],
        "friendship": ["Friendship is a relationship of mutual affection between people. Friends provide support, companionship, and emotional connection.", "Healthy friendships involve trust, respect, communication, and mutual support. Friends enrich life, provide different perspectives, and help through challenges."],
        "family": ["Family is a fundamental social unit, typically consisting of parents and children, but can include extended family and chosen family.", "Family provides support, identity, and belonging. Family structures vary across cultures and can include biological, adoptive, and chosen relationships."],
        "time": ["Time is the continuous progression of existence from past to present to future. It's measured in seconds, minutes, hours, days, years, and beyond.", "Time management is important for productivity and well-being. Understanding time helps in planning, setting goals, and making the most of life."],
        "life": ["Life is the condition that distinguishes organisms from inorganic matter. It's characterized by growth, reproduction, metabolism, and response to stimuli.", "Life on Earth is diverse, from microscopic organisms to complex beings. Understanding life involves biology, ecology, and the search for meaning and purpose."],
        "death": ["Death is the end of life. It's a natural part of the life cycle. Different cultures and religions have various beliefs and practices around death.", "Coping with death involves grief, remembrance, and finding meaning. Advance care planning and discussions about end-of-life wishes are important aspects of life."],
        "god": ["God is a concept in many religions representing a supreme being or ultimate reality. Beliefs about God vary across religions and philosophies.", "Discussions about God involve theology, philosophy, and personal faith. Respecting diverse beliefs about the divine is important in a pluralistic world."],
        "meaning": ["Meaning refers to significance, purpose, or interpretation. Finding meaning in life is a fundamental human pursuit involving philosophy, psychology, and personal reflection.", "Sources of meaning: relationships, work, creativity, service, beliefs, and personal growth. Meaning gives life purpose and direction."],
        "purpose": ["Purpose is the reason for which something is done or created. Finding life's purpose involves self-reflection, exploring interests, and contributing to something larger than oneself.", "Purpose can change over time. It provides motivation, direction, and fulfillment. Many find purpose through relationships, work, passions, or helping others."],
        "success": ["Success is achieving desired goals or outcomes. It can be personal, professional, or academic. Success means different things to different people.", "Success factors: hard work, perseverance, learning from failure, setting goals, and maintaining balance. Redefining success personally is important for satisfaction."],
        "failure": ["Failure is not achieving a desired outcome. It's a natural part of learning and growth. Many successful people have experienced significant failures.", "Learning from failure involves reflection, adaptation, and resilience. Failure can provide valuable lessons and lead to future success if approached constructively."],
        "dream": ["Dreams can be aspirations and goals we want to achieve, or the mental experiences during sleep involving images, emotions, and sensations.", "Pursuing dreams requires planning, effort, and perseverance. Understanding sleep dreams is studied in psychology and neuroscience for insights into the mind."],
        "hope": ["Hope is a positive expectation and desire for something to happen. It provides motivation, resilience, and the ability to cope with challenges.", "Hope is important for mental health and well-being. It can be nurtured through positive thinking, setting goals, and finding support during difficult times."],
        "courage": ["Courage is the ability to face fear, danger, or difficulty with bravery. It involves acting despite fear and standing up for what's right.", "Courage can be physical or moral. It's essential for personal growth, defending values, and overcoming challenges. Courage is developed through practice and conviction."],
        "wisdom": ["Wisdom is the quality of having good judgment based on knowledge, experience, and understanding. It involves making sound decisions and seeing things clearly.", "Wisdom is developed through life experience, learning, reflection, and listening to others. It's valued across cultures and ages for guiding decisions and actions."],
        "truth": ["Truth is that which is in accordance with fact or reality. In philosophy, truth is a central concept involving correspondence, coherence, and pragmatic theories.", "Seeking truth involves critical thinking, evidence, and open-mindedness. Truth is important for trust, knowledge, and ethical decision-making."],
        "freedom": ["Freedom is the power or right to act, speak, or think as one wants without hindrance or restraint. Types: political freedom, personal freedom, and economic freedom.", "Freedom is a fundamental value in many societies. Balancing freedom with responsibility and respecting others' freedom is important for social harmony."],
        "peace": ["Peace is a state of tranquility, harmony, and absence of conflict. It can be internal (personal peace) or external (societal peace).", "Peace is essential for well-being and prosperity. Promoting peace involves conflict resolution, understanding, tolerance, and justice at personal and global levels."],
        
        # Conversational
        "thank": ["You're welcome! Is there anything else I can help you with?", "Happy to help! Let me know if you have more questions.", "No problem! Feel free to ask anything else."],
        "bye": ["Goodbye! Have a great day!", "See you later! Feel free to come back if you have more questions.", "Take care!"],
        "sorry": ["No need to apologize! Feel free to ask or clarify anything.", "It's completely fine. What would you like to know?"],
        "good": ["That's great to hear! How can I assist you further?", "Good! What else would you like to discuss?"],
        "bad": ["I'm sorry to hear that. Is there something I can help you with?", "That's unfortunate. Feel free to share more if you'd like."],
        "joke": [
            "Why do programmers prefer dark mode? Because light attracts bugs! 😄",
            "Why did the developer go broke? Because he used up all his cache! 😄",
            "There are only 10 types of people in the world: those who understand binary and those who don't! 😄",
            "Why was the math book sad? Because it had too many problems! 😄",
            "What do you call a fake noodle? An impasta! 😄"
        ],
        "help": ("I can help you with almost any question! Here are some topics I know about:\n\n"
                 "**Project-Specific:**\n"
                 "- Fraud detection and risk scores\n"
                 "- Transaction analysis\n"
                 "- Machine learning models\n\n"
                 "**General Knowledge:**\n"
                 "- Science (physics, chemistry, biology)\n"
                 "- History and geography\n"
                 "- Programming and technology\n"
                 "- Arts, music, literature\n"
                 "- Sports and entertainment\n"
                 "- Health and psychology\n"
                 "- Society, culture, philosophy\n"
                 "- Environment and space\n"
                 "- And much more!\n\n"
                 "Just ask me anything!"),
    }
    
    # Pattern matching for common questions - check these FIRST before general topics
    if "how" in prompt_lower and "work" in prompt_lower:
        return "To explain how something works, I need more specific information. Could you tell me what you're curious about? For example: 'How does machine learning work?', 'How does the internet work?', or 'How do plants make food'?"
    
    if "what is" in prompt_lower:
        match = re.search(r"what is (.+)", prompt_lower)
        if match:
            subject = match.group(1).strip()
            # Check if it's in our knowledge base
            for topic in general_responses.keys():
                if topic in subject or subject in topic:
                    return general_responses[topic][0] if isinstance(general_responses[topic], list) else general_responses[topic]
            return f"I'd be happy to explain what {subject} is! However, I have limited knowledge in local mode. I can help with topics like science, history, geography, programming, technology, arts, sports, health, and more. Could you be more specific?"
    
    if "how to" in prompt_lower or "how do" in prompt_lower or "how can" in prompt_lower:
        # Try to identify the action
        if "learn" in prompt_lower:
            return "To learn effectively: 1) Start with basics, 2) Practice regularly, 3) Build projects, 4) Learn from mistakes, 5) Stay consistent. Specific topic-specific resources can help accelerate learning."
        if "lose" in prompt_lower and "weight" in prompt_lower:
            return "To lose weight: maintain a calorie deficit, exercise regularly, eat balanced meals, stay hydrated, and get enough sleep. Consult a healthcare professional for personalized advice."
        if "make" in prompt_lower:
            return "To make something depends on what you want to create. For software: learn programming, for food: follow recipes, for art: practice techniques. Be more specific about what you want to make!"
        if "solve" in prompt_lower:
            return "To solve problems: 1) Understand the problem clearly, 2) Break it into smaller parts, 3) Try different approaches, 4) Learn from failures, 5) Ask for help when stuck."
        if "write" in prompt_lower:
            return "To write well: practice regularly, read widely, plan your content, edit carefully, and get feedback. Whether it's code, essays, or stories, the key is consistent practice."
        if "create" in prompt_lower:
            return "To create something: start with an idea, plan the steps, gather resources, execute systematically, and iterate based on feedback. Creativity comes from practice and experimentation."
        return "I can help with 'how to' questions! Please specify what you'd like to do. For example: 'how to learn Python', 'how to cook pasta', or 'how to start a business'."
    
    # Then check general topics (for general knowledge) - improved matching
    # Check for exact topic match first
    for topic, answers in general_responses.items():
        if topic in prompt_lower:
            if isinstance(answers, str):
                return answers
            return "\n\n".join(answers[:2])
    
    # Then check project-specific topics (only for explicit project questions)
    for topic, answers in project_responses.items():
        if topic in prompt_lower:
            return "\n\n".join(answers[:2])
    if "how" in prompt_lower and "work" in prompt_lower:
        return "To explain how something works, I need more specific information. Could you tell me what you're curious about? For example: 'How does machine learning work?', 'How does the internet work?', or 'How do plants make food?'"
    
    if "what is" in prompt_lower:
        match = re.search(r"what is (.+)", prompt_lower)
        if match:
            subject = match.group(1).strip()
            # Check if it's in our knowledge base
            for topic in general_responses.keys():
                if topic in subject or subject in topic:
                    return general_responses[topic][0] if isinstance(general_responses[topic], list) else general_responses[topic]
            return f"I'd be happy to explain what {subject} is! However, I have limited knowledge in local mode. I can help with topics like science, history, geography, programming, technology, arts, sports, health, and more. Could you be more specific?"
    
    if "how to" in prompt_lower or "how do" in prompt_lower or "how can" in prompt_lower:
        # Try to identify the action
        if "learn" in prompt_lower:
            return "To learn effectively: 1) Start with basics, 2) Practice regularly, 3) Build projects, 4) Learn from mistakes, 5) Stay consistent. Specific topic-specific resources can help accelerate learning."
        if "lose" in prompt_lower and "weight" in prompt_lower:
            return "To lose weight: maintain a calorie deficit, exercise regularly, eat balanced meals, stay hydrated, and get enough sleep. Consult a healthcare professional for personalized advice."
        if "make" in prompt_lower:
            return "To make something depends on what you want to create. For software: learn programming, for food: follow recipes, for art: practice techniques. Be more specific about what you want to make!"
        if "solve" in prompt_lower:
            return "To solve problems: 1) Understand the problem clearly, 2) Break it into smaller parts, 3) Try different approaches, 4) Learn from failures, 5) Ask for help when stuck."
        if "write" in prompt_lower:
            return "To write well: practice regularly, read widely, plan your content, edit carefully, and get feedback. Whether it's code, essays, or stories, the key is consistent practice."
        if "create" in prompt_lower:
            return "To create something: start with an idea, plan the steps, gather resources, execute systematically, and iterate based on feedback. Creativity comes from practice and experimentation."
        return "I can help with 'how to' questions! Please specify what you'd like to do. For example: 'how to learn Python', 'how to cook pasta', or 'how to start a business'."
    
    if "who" in prompt_lower and "you" in prompt_lower:
        return "I am FraudGuard AI, an assistant that can answer questions about this fraud detection project and general topics without needing an internet connection. I have knowledge about science, history, geography, technology, arts, sports, and much more!"
    
    if "can you" in prompt_lower:
        return "I can help answer questions about many topics! I know about science, history, geography, programming, AI, technology, arts, music, sports, health, psychology, philosophy, environment, space, and general knowledge. What would you like to know?"
    
    if "why" in prompt_lower:
        if "sky" in prompt_lower and "blue" in prompt_lower:
            return "The sky appears blue because of Rayleigh scattering. Sunlight contains all colors, but blue light has a shorter wavelength and scatters more in the atmosphere, making the sky look blue."
        if "need" in prompt_lower and "sleep" in prompt_lower:
            return "We need sleep because it allows our bodies to repair themselves, our brains to process information and consolidate memories, and our immune systems to function properly. Lack of sleep can affect health, mood, and cognitive performance."
        if "earth" in prompt_lower and "round" in prompt_lower:
            return "Earth is round (spherical) because gravity pulls everything toward the center, creating a spherical shape. This shape also explains why Earth has a gravitational field that keeps objects on its surface."
        if "important" in prompt_lower:
            return "The importance depends on context. Many things are important: health, education, relationships, work, and personal growth. Could you specify what you're asking about why it's important?"
        return "That's a good 'why' question! To give you a helpful answer, I need more context. Could you provide more details about what you're asking about? For example: 'Why is the sky blue?' or 'Why do we need sleep?'"
    
    if "tell me" in prompt_lower:
        return "I'd be happy to tell you about something! Please specify what you'd like to know. I can share information about science, history, geography, technology, arts, sports, health, and many other topics."
    
    if "meaning" in prompt_lower:
        return "Meaning can refer to different things: the definition of a word, the significance of something, or the purpose of life. Could you clarify what meaning you're asking about?"
    
    if "best" in prompt_lower:
        return "Determining what's 'best' depends on context and personal preferences. Could you specify what you're comparing? For example: 'best programming language', 'best exercise', or 'best movie'?"
    
    if "difference" in prompt_lower:
        if "ai" in prompt_lower and "ml" in prompt_lower:
            return "AI (Artificial Intelligence) is the broader field of creating intelligent machines, while ML (Machine Learning) is a subset of AI where computers learn from data without explicit programming. All ML is AI, but not all AI is ML."
        if "java" in prompt_lower and "python" in prompt_lower:
            return "Java is statically typed, compiled, and runs on JVM - good for enterprise apps. Python is dynamically typed, interpreted, and has simpler syntax - good for data science, AI, and scripting. Python is generally easier to learn."
        if "sql" in prompt_lower and "nosql" in prompt_lower:
            return "SQL databases use structured tables with fixed schemas (MySQL, PostgreSQL). NoSQL databases use flexible schemas for unstructured data (MongoDB, Redis). SQL is better for structured data and complex queries, NoSQL for flexible, rapidly changing data."
        return "To explain the difference between two things, I need to know what you're comparing. Could you specify what you'd like me to compare?"
    
    # More pattern matching
    if "which" in prompt_lower:
        if "better" in prompt_lower:
            return "What's 'better' depends on your needs and context. Could you specify what you're comparing and what your requirements are? For example: 'which is better for beginners: Python or Java?'"
        return "To help you choose, I need to know what options you're considering and what you're trying to achieve. Could you provide more details?"
    
    if "recommend" in prompt_lower or "suggest" in prompt_lower:
        return "I can provide recommendations! Please tell me what you need suggestions for - whether it's books, tools, courses, or anything else, and I'll do my best to help."
    
    if "explain" in prompt_lower:
        return "I'd be happy to explain something! Please specify what topic or concept you'd like me to explain in more detail."
    
    if "define" in prompt_lower:
        return "I can provide definitions! Please tell me what term or concept you'd like me to define."
    
    if "list" in prompt_lower:
        if "countries" in prompt_lower:
            return "There are 195 recognized countries in the world. Some major ones: USA, India, China, Russia, Brazil, UK, Germany, France, Japan, Australia, and many more across different continents."
        if "programming" in prompt_lower and "language" in prompt_lower:
            return "Popular programming languages: Python (AI/data science), JavaScript (web), Java (enterprise), C++ (systems), C# (Windows), Go (cloud), Swift (iOS), Kotlin (Android), and many others."
        return "I can provide lists! Please specify what you'd like me to list."
    
    # Handle simple greetings and small talk
    if "good morning" in prompt_lower:
        return "Good morning! How can I help you today?"
    if "good afternoon" in prompt_lower:
        return "Good afternoon! What would you like to know?"
    if "good evening" in prompt_lower:
        return "Good evening! How can I assist you?"
    if "good night" in prompt_lower:
        return "Good night! Have a great rest. Feel free to come back anytime if you have questions."
    
    # Common questions
    if "weather" in prompt_lower:
        return "I don't have access to real-time weather data, but I can explain weather concepts! Weather is the state of the atmosphere at a specific time and place, including temperature, humidity, wind, and precipitation. For current weather, check a weather app or website."
    
    if "time" in prompt_lower and "now" in prompt_lower:
        return "I don't have access to real-time data. Please check your device's clock or a world clock website for the current time."
    
    if "date" in prompt_lower and "today" in prompt_lower:
        return "I don't have access to real-time data. Please check your device's calendar for today's date."
    
    if "news" in prompt_lower:
        return "I don't have access to real-time news. For current news, please visit news websites like BBC, CNN, or local news sources. I can explain news concepts or historical events though!"
    
    if "recipe" in prompt_lower:
        return "I can provide general cooking guidance! To follow a recipe: 1) Read it completely first, 2) Gather ingredients, 3) Follow steps in order, 4) Measure accurately, 5) Adjust seasonings to taste. For specific recipes, cooking websites or apps are great resources."
    
    # Default response - more helpful
    return ("I'm here to help! While I'm a local AI with limited knowledge, I can answer questions about many topics:\n\n"
            "**Project Questions:**\n"
            "- Fraud detection and risk analysis\n"
            "- Machine learning models\n"
            "- Transaction security\n\n"
            "**General Knowledge:**\n"
            "- Science (physics, chemistry, biology)\n"
            "- History and geography\n"
            "- Programming and technology\n"
            "- Arts, music, literature\n"
            "- Sports and entertainment\n"
            "- Health and psychology\n"
            "- Society, culture, philosophy\n"
            "- Environment and space\n\n"
            "**I can also help with:**\n"
            "- 'How to' questions\n"
            "- 'Why' questions\n"
            "- Definitions and explanations\n"
            "- Comparisons and differences\n"
            "- Recommendations\n\n"
            "Try asking more specific questions like: 'What is machine learning?', 'How does the internet work?', or 'Explain quantum physics'!")


def show_fraudguard_ai():
    st.markdown("""
    <style>
    .fg-title {
        background: linear-gradient(120deg, #062654, #087fe8);
        color: white;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="fg-title"><h2>🤖 FraudGuard AI</h2>'
        '<p>Local AI Assistant - Ask anything! No internet required!</p></div>',
        unsafe_allow_html=True
    )

    if "fg_messages" not in st.session_state:
        st.session_state.fg_messages = [
            {
                "role": "assistant",
                "content": "Hi! I am FraudGuard AI, running in local mode without any API or internet connection. I can answer questions about this fraud detection project and almost any general topic - science, history, geography, programming, technology, arts, sports, health, philosophy, and more. Ask me anything!"
            }
        ]

    for message in st.session_state.fg_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask FraudGuard AI a question...")

    if prompt:
        st.session_state.fg_messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get local response
        answer = get_local_response(prompt)
        
        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.fg_messages.append(
            {"role": "assistant", "content": answer}
        )

    if st.button("Clear chat", key="fg_clear_chat"):
        st.session_state.fg_messages = []
        st.rerun()
