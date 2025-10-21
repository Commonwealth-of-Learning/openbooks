# OpenBooks

A digitized collection of Open Educational Resources (OER) from the Commonwealth of Learning's PressBooks platform.

## 📚 Overview

OpenBooks collects PressBooks titles that have been converted to simple
static sites.  Each folder in the repository contains a complete copy of
an open textbook that can be viewed in any modern web browser.

## 🚀 Getting Started

1. **Install dependencies**

   ```bash
   pip install -r PBConverter/requirements.txt
   ```

2. **Convert a PressBooks title** using the converter script.  Provide the
   source URL and an output directory:

   ```bash
   python PBConverter/pb_converter.py --url "https://example.com/book" --output "output_dir"
   ```

3. **Convert a Moodle backup** (`.mbz`) using the Moodle converter.  Supply
   the path to the backup archive and an output directory:

   ```bash
   python PBConverter/moodle_converter.py convert --mbz path/to/course.mbz --output moodle_course
   ```

4. **View the generated site** by running a local web server inside the
   output directory:

   ```bash
   cd output_dir
   python -m http.server
   ```

   Then open <http://localhost:8000> in your browser.

This repository hosts open textbooks and educational materials that are:
- Freely accessible
- HTML-based
- Mobile responsive
- Licensed under Creative Commons
- Available for educational use worldwide


## 🔧 Technical Details

- Content structure based on HTML/CSS
- Responsive design principles
- Cross-platform compatibility
- Accessible formatting

## Available Resources

The repository includes the following open textbooks and resources. The
list below is generated automatically&mdash;please do not edit it by
hand. If you clone the repository, you can open `index.html` in the
repository root to browse the collection in your browser.

<!-- BEGIN AUTO-GENERATED RESOURCE LIST -->
- [A Policy Brief on MOOCs](policybriefonmoocs/index.html)
- [Advanced Cybersecurity Training for Teachers](advancedcybersecuritytrainingteachers/index.html)
- [Agricultural Statistics in Practice](agriculturalstatisticsinpractice/index.html)
- [Attain Food Security through Subsistence and Sustainable Agriculture](foodsecuritysustainableagriculture/index.html)
- [Basics of Entrepreneurship Development in Agriculture](basicsofentrepreneurship/index.html)
- [Climate Change and Climate Action](climatechangeclimateaction/index.html)
- [Climate Change and Its Impacts: Adaptation, Mitigation, and Climate Justice](climatechangeandimpacts/index.html)
- [Connections (vol 28, no 3)](connectionsvol28no3/index.html)
- [Connections (vol. 27, no. 3)](connectionsvol27no3/index.html)
- [Connections (VOL. 28, NO. 1)](connectionsvol28no1/index.html)
- [Connections (vol. 28, no. 2)](connectionsvol28no2/index.html)
- [Conservation Agriculture-based Sustainable Intensification](casi/index.html)
- [Creating Gender-Sensitive, Climate-Responsive, Sustainable Livelihoods to Build Self-Reliant, Resilient Local Economies](genderclimatesustainablelivelihoods/index.html)
- [Current Trends in Treatment and Control of Parasitic Diseases of Livestock and Poultry](treatmentandcontrolparasiticdiseaseslivestockpoultry/index.html)
- [Cybersecurity Training for Teachers](cybersecuritytrainingteachers/index.html)
- [Design Thinking for Agricultural Implements](designthinking/index.html)
- [Detection, Diagnosis and Management of Plant Diseases](managementofplantdiseases/index.html)
- [e-Extension](eextension/index.html)
- [Fluid Therapy and Management of Clinical Syndrome in Cattle and Small Ruminants](fluidtherapycattlesmallruminants/index.html)
- [Functional Foods: Concept, Technology and Health Benefits](functionalfoods/index.html)
- [Fundamentals of Agricultural Extension](fundamentalsofagextn/index.html)
- [Gender Equality in the Context of Climate Change and Food Security](genderequalityclimatechangefoodsecurity/index.html)
- [Guide to Blended Learning](blendedlearning/index.html)
- [Integrated Disease Management](integrateddiseasemanagement/index.html)
- [Integrated Pest Management (IPM)](integratedpestmanagement/index.html)
- [Learning Analytics: A Primer](learninganalyticsaprimer/index.html)
- [Management of Infertility in Cattle](managementinfertilitycattle/index.html)
- [Management of Metabolic and Production Disorders in Cattle](metabolicandproductiondisorderscattle/index.html)
- [Practical Animal Nutrition for Augmenting Livestock and Poultry Productivity](animalnutritionforlivestockandpoultryproductivity/index.html)
- [Resource Management in Rainfed Drylands](resourcemanagementrainfeddrylands/index.html)
- [Respecting Indigenous Rights and Practices: Ways to a Better Planet](respectingindigenousrightsandpractices/index.html)
- [Statistical Techniques for Agriculturists](statisticaltechniquesforagriculturists/index.html)
- [Universal Design for Learning](universaldesignforlearning/index.html)
- [Using Innovations and Climate-Responsive Actions to Build Community Resilience](climateresponsiveactionscommunityresilience/index.html)
- [Value Engineering Agricultural Plan](valueengineeringagriculturalplan/index.html)
<!-- END AUTO-GENERATED RESOURCE LIST -->

## Running the Converter

1. Install the required dependencies:

   ```bash
   pip install -r PBConverter/requirements.txt
   ```

2. Convert a PressBooks title by specifying its URL and an output directory:

   ```bash
   python PBConverter/pb_converter.py --url "https://example.com/book" --output "output_directory"
   ```

3. Start a simple server in the output directory to view the static copy:

   ```bash
   cd output_directory
   python -m http.server
   ```

   Then visit <http://localhost:8000> in your browser.

## Updating the Resource List

The list of available resources in this README is generated
automatically. Whenever new books are added or removed, run the helper
script to update the section:

```bash
python scripts/update_readme.py
```

This will scan the repository for book folders containing an
`index.html` file and refresh the bullet list between the `BEGIN` and
`END` markers in `README.md`.

## 📝 License

This work is licensed under [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).

## 🤝 Contributing

Contributions are welcome! If you encounter issues or have ideas for
new features, feel free to open an issue or submit a pull request on
GitHub.

## 📫 Contact

**Commonwealth of Learning**
- 📍 505 Burrard Street, Suite 1650, Box 5 Vancouver, BC V7X 1M6, Canada
- 📞 +1.604.775.8200
- 📧 info@col.org
- 🌐 [www.col.org](https://www.col.org)
