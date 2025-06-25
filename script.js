// Resource data array - Easy to maintain and update
const resources = [
    {
        category: "climate",
        url: "climatechangeandimpacts/index.html",
        thumbnail: "climatechangeandimpacts/climatechangeandimpacts/wp-content/uploads/sites/52/2024/12/ClimateChangeImpactCover-350x467.jpg",
        subject: "Climate Science",
        title: "Climate Change and Its Impacts: Adaptation, Mitigation, and Climate Justice",
        description: "Focus on strategies for adapting to climate change's impacts, mitigating its consequences, and addressing climate justice issues.",
        authors: "Commonwealth of Learning",
        updated: "02/12/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "resourcemanagementrainfeddrylands/index.html",
        thumbnail: "resourcemanagementrainfeddrylands/resourcemanagementrainfeddrylands/wp-content/uploads/sites/51/2024/11/AgMOOCs_Nov20246-350x467.jpg",
        subject: "Agricultural Science",
        title: "Resource Management in Rainfed Drylands",
        description: "Comprehensive guide to dryland agriculture covering 67% of India's cultivated area with latest technological innovations.",
        authors: "Dr G. M. Sujith",
        updated: "02/12/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "statisticaltechniquesforagriculturists/index.html",
        thumbnail: "statisticaltechniquesforagriculturists/statisticaltechniquesforagriculturists/wp-content/uploads/sites/50/2024/11/AgMOOCs_Nov20245-350x467.jpg",
        subject: "Agricultural Statistics",
        title: "Statistical Techniques for Agriculturists",
        description: "Essential training in agricultural statistics covering data collection, analysis, and modern applications.",
        authors: "Prof J Ramkumar, Dr Amandeep Singh",
        updated: "02/12/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "valueengineeringagriculturalplan/index.html",
        thumbnail: "valueengineeringagriculturalplan/valueengineeringagriculturalplan/wp-content/uploads/sites/48/2024/11/AgMOOCs_Nov20243-350x467.jpg",
        subject: "Agricultural Engineering",
        title: "Value Engineering Agricultural Plan",
        description: "Systematic problem-solving and cost-effective optimization techniques for agricultural machinery and equipment.",
        authors: "Prof J. Ramkumar, Dr Amandeep Singh",
        updated: "02/12/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "integratedpestmanagement/index.html",
        thumbnail: "integratedpestmanagement/integratedpestmanagement/wp-content/uploads/sites/49/2024/11/AgMOOCs_Nov20244-350x467.jpg",
        subject: "Pest Management",
        title: "Integrated Pest Management (IPM)",
        description: "Comprehensive guide to sustainable pest control covering legal, ecological, cultural, biological, and chemical approaches.",
        authors: "Prof Prabhuraj A., Prof M. Bheemanna, Prof B.V. Patil",
        updated: "02/12/2024",
        license: "CC BY-SA"
    },
    {
        category: "veterinary",
        url: "treatmentandcontrolparasiticdiseaseslivestockpoultry/index.html",
        thumbnail: "treatmentandcontrolparasiticdiseaseslivestockpoultry/treatmentandcontrolparasiticdiseaseslivestockpoultry/wp-content/uploads/sites/47/2024/11/AgMOOCs_Nov20242-350x467.jpg",
        subject: "Veterinary Medicine",
        title: "Current Trends in Treatment and Control of Parasitic Diseases of Livestock and Poultry",
        description: "Advanced guide to parasitic disease management in livestock focusing on economic efficiency and diagnostic techniques.",
        authors: "Dr N. K. Sudeep Kumar, Dr Bhaskaran Ravi Latha, et al.",
        updated: "02/12/2024",
        license: "CC BY-SA"
    },
    {
        category: "climate",
        url: "respectingindigenousrightsandpractices/index.html",
        thumbnail: "respectingindigenousrightsandpractices/respectingindigenousrightsandpractices/wp-content/uploads/sites/45/2024/07/24_EWG_course_6-350x467.jpg",
        subject: "Indigenous Rights",
        title: "Respecting Indigenous Rights and Practices: Ways to a Better Planet",
        description: "Course for field workers on Indigenous community conservation practices and rights.",
        authors: "Dr Sundari Ramakrishna",
        updated: "03/10/2024",
        license: "CC BY-SA"
    },
    {
        category: "climate",
        url: "climateresponsiveactionscommunityresilience/index.html",
        thumbnail: "climateresponsiveactionscommunityresilience/climateresponsiveactionscommunityresilience/wp-content/uploads/sites/44/2024/07/24_EWG_course_5-350x467.jpg",
        subject: "Community Resilience",
        title: "Using Innovations and Climate-Responsive Actions to Build Community Resilience",
        description: "Explores alternative sustainable livelihoods and innovation models for climate resilience.",
        authors: "Sundari Ramakrishna",
        updated: "17/09/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "functionalfoods/index.html",
        thumbnail: "functionalfoods/functionalfoods/wp-content/uploads/sites/17/2023/03/Annotation-2019-11-19-152426-350x163.png",
        subject: "agMOOCs",
        title: "Functional Foods: Concept, Technology and Health Benefits",
        description: "Due to increased cost of health-care and lifestyle related diseases, consumers are shifting towards functional foods.",
        authors: "Center for Development of Technical Education, IIT Kanpur",
        updated: "13/08/2024",
        license: "CC BY-NC"
    },
    {
        category: "education",
        url: "universaldesignforlearning/index.html",
        thumbnail: "universaldesignforlearning/universaldesignforlearning/wp-content/uploads/sites/8/2023/02/UDL-Cover-350x487.png",
        subject: "Education",
        title: "Universal Design for Learning",
        description: "Introductory course on Universal Design for Learning (UDL) developed using Accessibility Toolkit.",
        authors: "Josie Gray",
        updated: "05/2021",
        license: "CC BY"
    },
    {
        category: "gender",
        url: "genderclimatesustainablelivelihoods/index.html",
        thumbnail: "genderclimatesustainablelivelihoods/genderclimatesustainablelivelihoods/wp-content/uploads/sites/43/2024/07/24_EWG_microcourses_rev14-350x467.jpg",
        subject: "Gender & Economics",
        title: "Creating Gender-Sensitive, Climate-Responsive, Sustainable Livelihoods",
        description: "Comprehensive guide to developing gender-sensitive livelihoods for climate resilience.",
        authors: "Kuntal De",
        updated: "17/09/2024",
        license: "CC BY-SA"
    },
    {
        category: "food",
        url: "foodsecuritysustainableagriculture/index.html",
        thumbnail: "foodsecuritysustainableagriculture/foodsecuritysustainableagriculture/wp-content/uploads/sites/40/2024/07/24_EWG_course_2-350x467.jpg",
        subject: "Food Security",
        title: "Attain Food Security through Subsistence and Sustainable Agriculture",
        description: "Examines climate change effects on food security and presents sustainable agriculture innovations.",
        authors: "Marlene Johnson",
        updated: "17/09/2024",
        license: "CC BY-SA"
    },
    {
        category: "gender",
        url: "genderequalityclimatechangefoodsecurity/index.html",
        thumbnail: "genderequalityclimatechangefoodsecurity/genderequalityclimatechangefoodsecurity/wp-content/uploads/sites/41/2024/07/24_EWG_course_3-350x467.jpg",
        subject: "Gender & Climate",
        title: "Gender Equality in the Context of Climate Change and Food Security",
        description: "Explores how gender roles affect climate change mitigation and women's leadership in conservation.",
        authors: "Marlene Johnson",
        updated: "17/09/2024",
        license: "CC BY-SA"
    },
    {
        category: "veterinary",
        url: "fluidtherapycattlesmallruminants/index.html",
        thumbnail: "fluidtherapycattlesmallruminants/fluidtherapycattlesmallruminants/wp-content/uploads/sites/30/2023/12/AgMOOC_3-350x467.jpg",
        subject: "Veterinary Medicine",
        title: "Fluid Therapy and Management of Clinical Syndrome in Cattle and Small Ruminants",
        description: "Essential course on fluid therapy for ruminant health management.",
        authors: "Dr N.K. Sudeep Kumar, Dr G. Vijayakumar, et al.",
        updated: "18/07/2024",
        license: "CC BY-SA"
    },
    {
        category: "veterinary",
        url: "managementinfertilitycattle/index.html",
        thumbnail: "managementinfertilitycattle/managementinfertilitycattle/wp-content/uploads/sites/29/2023/12/AgMOOC_4-350x467.jpg",
        subject: "Animal Husbandry",
        title: "Management of Infertility in Cattle",
        description: "Comprehensive agMOOCs covering six critical infertility topics including repeat breeding syndrome.",
        authors: "Dr N.K. Sudeep Kumar, Dr M. Selvaraju, et al.",
        updated: "18/07/2024",
        license: "CC BY-SA"
    },
    {
        category: "technology",
        url: "designthinking/index.html",
        thumbnail: "designthinking/designthinking/wp-content/uploads/sites/23/2023/09/AgMOOCs-350x467.jpg",
        subject: "Design & Engineering",
        title: "Design Thinking for Agricultural Implements",
        description: "Introduction to creative design processes for agricultural equipment development.",
        authors: "Professor J Ramkumar, Dr Amandeep Singh",
        updated: "31/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "eextension/index.html",
        thumbnail: "eextension/eextension/wp-content/uploads/sites/24/2023/09/AgMOOCs2-350x467.jpg",
        subject: "Extension Education",
        title: "e-Extension",
        description: "Revolutionary approach to agricultural extension using ICT.",
        authors: "Professor Basavaprabhu Jirli",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "casi/index.html",
        thumbnail: "casi/casi/wp-content/uploads/sites/25/2023/09/AgMOOCs3-350x467.jpg",
        subject: "Sustainable Agriculture",
        title: "Conservation Agriculture-based Sustainable Intensification",
        description: "CASI approach including zero tillage, mechanized crop establishment, and improved nutrition management.",
        authors: "Dr. Ram Datt, Dr. Sanjay Kumar, Dr. Mahesh K. Gathala",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "managementofplantdiseases/index.html",
        thumbnail: "managementofplantdiseases/managementofplantdiseases/wp-content/uploads/sites/26/2023/09/AgMOOCs4-350x467.jpg",
        subject: "Plant Pathology",
        title: "Detection, Diagnosis and Management of Plant Diseases",
        description: "Comprehensive guide to plant disease diagnostics covering conventional and molecular techniques.",
        authors: "Dr. Birinchi Kumar Sarma",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "agriculturalstatisticsinpractice/index.html",
        thumbnail: "agriculturalstatisticsinpractice/agriculturalstatisticsinpractice/wp-content/uploads/sites/28/2023/09/AgMOOCs5-350x467.jpg",
        subject: "Agricultural Statistics",
        title: "Agricultural Statistics in Practice",
        description: "Practical application of statistical methods in agriculture with emphasis on descriptive and predictive analyses.",
        authors: "Prof. J. Ramkumar, Dr. Amandeep Singh",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "veterinary",
        url: "metabolicandproductiondisorderscattle/index.html",
        thumbnail: "metabolicandproductiondisorderscattle/metabolicandproductiondisorderscattle/wp-content/uploads/sites/31/2023/12/AgMOOC_-350x467.jpg",
        subject: "Veterinary Medicine",
        title: "Management of Metabolic and Production Disorders in Cattle",
        description: "Advanced veterinary course covering ketosis, milk fever, mastitis, and other metabolic disorders.",
        authors: "Dr N. K. Sudeep Kumar, Dr S. Kavitha, et al.",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "agriculture",
        url: "integrateddiseasemanagement/index.html",
        thumbnail: "integrateddiseasemanagement/integrateddiseasemanagement/wp-content/uploads/sites/35/2024/01/AgMOOCs6-350x467.jpg",
        subject: "Plant Pathology",
        title: "Integrated Disease Management",
        description: "Billion-dollar crop loss prevention through integrated disease management strategies.",
        authors: "Professor B. K. Sarma",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "veterinary",
        url: "animalnutritionforlivestockandpoultryproductivity/index.html",
        thumbnail: "animalnutritionforlivestockandpoultryproductivity/animalnutritionforlivestockandpoultryproductivity/wp-content/uploads/sites/32/2023/12/AgMOOC_2-350x467.jpg",
        subject: "Animal Nutrition",
        title: "Practical Animal Nutrition for Augmenting Livestock and Poultry Productivity",
        description: "Vital course focused on principles and practices of animal nutrition for all stakeholders.",
        authors: "Dr. N. K. Sudeep Kumar, Dr. C. Valli, et al.",
        updated: "29/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "education",
        url: "policybriefonmoocs/index.html",
        thumbnail: "policybriefonmoocs/policybriefonmoocs/wp-content/uploads/sites/14/2023/03/policy_brief-350x452.png",
        subject: "Open Education",
        title: "A Policy Brief on MOOCs",
        description: "Comprehensive policy recommendations for educational institutions considering MOOCs implementation.",
        authors: "David Porter, Russell Beale",
        updated: "21/03/2024",
        license: "CC BY-SA"
    },
    {
        category: "education",
        url: "advancedcybersecuritytrainingteachers/index.html",
        thumbnail: "advancedcybersecuritytrainingteachers/advancedcybersecuritytrainingteachers/wp-content/uploads/sites/22/2023/07/ACTT-cover-350x467.jpg",
        subject: "Cybersecurity",
        title: "Advanced Cybersecurity Training for Teachers",
        description: "High-level course for educators with advanced skills to defend against cyber threats.",
        authors: "Knowledge Services Manager",
        updated: "17/07/2023",
        license: "CC BY-SA"
    },
    {
        category: "education",
        url: "cybersecuritytrainingteachers/index.html",
        thumbnail: "cybersecuritytrainingteachers/cybersecuritytrainingteachers/wp-content/uploads/sites/20/2023/06/CTTcover-350x467.jpg",
        subject: "Cybersecurity",
        title: "Cybersecurity Training for Teachers",
        description: "Introductory course providing essential online safety knowledge for educators and parents.",
        authors: "Betty Ogange, Knowledge Services Manager",
        updated: "17/07/2023",
        license: "CC BY-SA"
    },
    {
        category: "education",
        url: "blendedlearning/index.html",
        thumbnail: "blendedlearning/blendedlearning/wp-content/uploads/sites/13/2023/03/2019-03-15-17_02_00-2018_Cleveland-Innes-Wilton_Guide-to-Blended-Learning.pdf-350x451.png",
        subject: "Blended Learning",
        title: "Guide to Blended Learning",
        description: "Introduction to combining technology and distance education strategies with traditional classroom activities.",
        authors: "Martha, Dan",
        updated: "01/03/2023",
        license: "CC BY-SA"
    },
    {
        category: "climate",
        url: "climatechangeclimateaction/index.html",
        thumbnail: "climatechangeclimateaction/climatechangeclimateaction/wp-content/uploads/sites/39/2024/07/24_EWG_course_1-350x467.jpg",
        subject: "Climate Change",
        title: "Climate Change and Climate Action",
        description: "This course explains climate change and its impact on human lives from a local context.",
        authors: "Madhavi Joshi",
        updated: "17/09/2024",
        license: "CC BY"
    }
];

// Function to create resource card HTML
function createResourceCard(resource) {
    return `
        <div class="resource-card" data-category="${resource.category}" data-searchable="${resource.title.toLowerCase()} ${resource.authors.toLowerCase()} ${resource.subject.toLowerCase()}">
            <a href="${resource.url}" class="resource-card-link" target="_blank" rel="noopener noreferrer">
                <div class="card-header">
                    <img src="${resource.thumbnail}" alt="Cover of ${resource.title}" class="resource-thumbnail">
                    <div class="card-header-content">
                        <div class="subject-tag">${resource.subject}</div>
                        <h3>${resource.title}</h3>
                    </div>
                </div>
                <div class="card-body">
                    <p>${resource.description}</p>
                    <div class="card-meta">
                        <span class="authors">${resource.authors}</span>
                        <span class="license-badge">${resource.license}</span>
                    </div>
                </div>
            </a>
        </div>
    `;
}

// Initialize catalog
function initializeCatalog() {
    const catalogGrid = document.getElementById('catalogGrid');
    // Sort resources alphabetically by title
    const sortedResources = [...resources].sort((a, b) =>
        a.title.localeCompare(b.title)
    );
    catalogGrid.innerHTML = sortedResources.map(resource => createResourceCard(resource)).join('');
    updateCounts();
}

// Filter functionality
function filterBooks(category) {
    const cards = document.querySelectorAll('.resource-card');
    const buttons = document.querySelectorAll('.filter-btn');

    buttons.forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.filter-btn[data-category="${category}"]`).classList.add('active');

    cards.forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Search functionality
function searchBooks() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const cards = document.querySelectorAll('.resource-card');

    cards.forEach(card => {
        const searchableText = card.dataset.searchable;
        if (searchableText.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Update counts
function updateCounts() {
    const totalEl = document.getElementById('total-count');
    totalEl.textContent = resources.length;

    const counts = {};
    resources.forEach(resource => {
        counts[resource.category] = (counts[resource.category] || 0) + 1;
    });

    const buttons = document.querySelectorAll('.filter-btn[data-category]');
    buttons.forEach(btn => {
        const cat = btn.dataset.category;
        const badge = btn.querySelector(`.count-badge[data-count-for="${cat}"]`);
        if (badge) {
            if (cat === 'all') {
                badge.textContent = resources.length;
            } else {
                badge.textContent = counts[cat] || 0;
            }
        }
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeCatalog();

    // Attach search event listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', searchBooks);
    }

    // Attach filter event listeners
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const category = event.currentTarget.dataset.category;
            filterBooks(category);
        });
    });
});