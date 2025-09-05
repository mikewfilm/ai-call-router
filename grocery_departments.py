# Comprehensive Grocery Store Department Routing
# This file contains all conceivable grocery items organized by department
import re

# ===== GROCERY DEPARTMENTS =====

# PRODUCE DEPARTMENT
PRODUCE_TERMS = r"""
    apple|apples|banana|bananas|orange|oranges|grape|grapes|strawberry|strawberries|blueberry|blueberries
    raspberry|raspberries|blackberry|blackberries|peach|peaches|pear|pears|plum|plums|cherry|cherries
    lemon|lemons|lime|limes|grapefruit|grapefruits|pineapple|pineapples|mango|mangoes|kiwi|kiwis
    avocado|avocados|tomato|tomatoes|potato|potatoes|onion|onions|garlic|carrot|carrots|celery
    lettuce|spinach|kale|arugula|romaine|iceberg|butter lettuce|spring mix|mixed greens
    broccoli|cauliflower|asparagus|brussels sprouts|green beans|snap peas|snow peas|zucchini
    yellow squash|eggplant|bell pepper|bell peppers|jalapeno|jalapenos|habanero|habaneros
    cucumber|cucumbers|radish|radishes|turnip|turnips|beet|beets|parsnip|parsnips|rutabaga
    sweet potato|sweet potatoes|yam|yams|butternut squash|acorn squash|spaghetti squash
    pumpkin|pumpkins|mushroom|mushrooms|portobello|shiitake|oyster mushrooms|white mushrooms
    corn|corn on the cob|ear of corn|fresh corn|baby corn|corn kernels
    green onion|green onions|scallion|scallions|chives|cilantro|parsley|basil|rosemary|thyme
    oregano|sage|mint|dill|bay leaves|fresh herbs|herbs|organic|conventional|pre cut|precut
    fruit|vegetable|vegetables|produce|fresh|ripe|unripe|organic produce
    
    # Produce brands
    dole|chiquita|del monte|fresh express|earthbound farm|organic valley|horizon organic
    simply organic|newman's own|annie's|stonyfield|chobani|fage|siggi's|noosa|ellenos
    bolthouse farms|naked juice|odwalla|suja|evolution fresh|suja juice|naked smoothie
    fresh thyme|whole foods|trader joe's|sprouts|kroger|safeway|albertsons|publix
"""

# DAIRY DEPARTMENT
DAIRY_TERMS = r"""
    milk|whole milk|skim milk|2% milk|1% milk|almond milk|soy milk|oat milk|coconut milk|cashew milk
    half and half|heavy cream|whipping cream|light cream|coffee creamer|non dairy creamer
    butter|unsalted butter|salted butter|margarine|spread|butter substitute|ghee
    cheese|cheddar|mozzarella|provolone|swiss|american|colby|monterey jack|pepper jack
    parmesan|romano|asiago|feta|blue cheese|gorgonzola|brie|camembert|goat cheese|cream cheese
    cottage cheese|ricotta|string cheese|cheese sticks|shredded cheese|sliced cheese|block cheese
    yogurt|greek yogurt|regular yogurt|vanilla yogurt|strawberry yogurt|blueberry yogurt|plain yogurt
    flavored yogurt|yogurt drink|kefir|probiotic|dairy free yogurt|non dairy yogurt
    eggs|egg|dozen eggs|organic eggs|cage free eggs|free range eggs|brown eggs|white eggs
    egg whites|egg yolks|liquid eggs|egg substitute|just egg|vegan eggs
    sour cream|crema|mexican cream|dip|ranch dip|onion dip|spinach dip|artichoke dip
    ice cream|vanilla ice cream|chocolate ice cream|strawberry ice cream|rocky road|cookie dough
    mint chocolate chip|coffee ice cream|pistachio|butter pecan|neapolitan|ice cream bars
    popsicles|ice cream sandwiches|frozen yogurt|sorbet|gelato|frozen treats
    
    # Dairy brands
    horizon|organic valley|stonyfield|chobani|fage|siggi's|noosa|ellenos|yoplait|dannon|activia
    dannon|oikos|chobani flip|chobani greek|chobani less sugar|chobani zero sugar
    tillamook|cabot|kraft|sargento|land o lakes|kerrygold|president|lucerne|great value|store brand
    silk|almond breeze|blue diamond|califia farms|oatly|planet oat|chobani oat|silk oat
    fairlife|lactaid|organic valley|horizon organic|maple hill|stonyfield organic
    ben and jerry's|haagen dazs|talenti|breyers|edys|dryers|blue bell|tillamook ice cream
    just egg|follow your heart|violife|daiya|so delicious|oatly|silk|almond breeze
"""

# MEAT & SEAFOOD DEPARTMENT
MEAT_SEAFOOD_TERMS = r"""
    beef|ground beef|hamburger|burger|steak|ribeye|sirloin|t bone|porterhouse|filet mignon
    flank steak|skirt steak|chuck roast|pot roast|brisket|short ribs|beef ribs|beef stew meat
    pork|pork chops|pork loin|pork tenderloin|pork roast|bacon|ham|prosciutto|pancetta|sausage
    italian sausage|bratwurst|kielbasa|chorizo|hot dogs|wieners|frankfurters|pork ribs|baby back ribs
    chicken|chicken breast|chicken thighs|chicken legs|chicken wings|whole chicken|rotisserie chicken
    turkey|turkey breast|turkey legs|turkey wings|ground turkey|turkey bacon|turkey sausage
    lamb|lamb chops|lamb leg|lamb shoulder|lamb stew meat|lamb ribs
    veal|veal chops|veal cutlets|veal stew meat
    fish|salmon|tilapia|cod|haddock|mahi mahi|tuna|swordfish|halibut|sea bass|red snapper|trout
    shrimp|prawns|crab|crab legs|crab meat|lobster|lobster tails|mussels|clams|oysters|scallops
    scallops|calamari|octopus|sushi|sashimi|fresh fish|frozen fish|wild caught|farm raised
    deli meat|deli turkey|deli ham|deli roast beef|deli chicken|deli salami|deli bologna
    pastrami|corned beef|roast beef|turkey breast|ham|salami|pepperoni|mortadella|capicola
    hot dogs|bologna|liverwurst|head cheese|pate|foie gras
    
    # Meat & Seafood brands
    perdue|tyson|foster farms|sanderson farms|bell and evans|mary's chicken|organic valley
    hormel|jimmy dean|johnsonville|hillshire farm|oscar mayer|ball park|nathan's|hebrew national
    boar's head|dietz and watson|land o frost|sara lee|hillshire farm|oscar mayer|kraft
    wild alaska|wild caught|farm raised|fresh catch|daily catch|seafood market
    tilapia|salmon|cod|haddock|mahi mahi|tuna|swordfish|halibut|sea bass|red snapper|trout
    shrimp|prawns|crab|crab legs|crab meat|lobster|lobster tails|mussels|clams|oysters|scallops
"""

# FROZEN DEPARTMENT
FROZEN_TERMS = r"""
    frozen pizza|frozen dinners|tv dinners|microwave meals|frozen entrees|frozen lasagna
    frozen burritos|frozen tacos|frozen enchiladas|frozen pasta|frozen ravioli|frozen tortellini
    frozen vegetables|frozen peas|frozen corn|frozen broccoli|frozen spinach|frozen mixed vegetables
    frozen fruit|frozen berries|frozen strawberries|frozen blueberries|frozen mango|frozen pineapple
    frozen waffles|frozen pancakes|frozen french toast|frozen breakfast sandwiches|frozen breakfast burritos
    frozen hash browns|frozen tater tots|frozen french fries|frozen onion rings|frozen mozzarella sticks
    frozen chicken nuggets|frozen chicken tenders|frozen fish sticks|frozen fish fillets|frozen shrimp
    frozen meatballs|frozen hamburger patties|frozen sausage|frozen bacon|frozen hot dogs
    frozen ice cream|frozen yogurt|frozen popsicles|frozen ice cream bars|frozen ice cream sandwiches
    frozen novelties|frozen desserts|frozen cakes|frozen pies|frozen cookies|frozen brownies
    frozen bread|frozen rolls|frozen bagels|frozen english muffins|frozen croissants|frozen danish
    frozen dough|frozen pizza dough|frozen bread dough|frozen cookie dough|frozen pie crust
    frozen appetizers|frozen spring rolls|frozen egg rolls|frozen dumplings|frozen potstickers
    frozen edamame|frozen edamame beans|frozen shelled edamame
    
    # Frozen brands
    stouffer's|lean cuisine|healthy choice|smart ones|banquet|swanson|hungry man|marie callender's
    digiorno|red baron|tombstone|freschetta|newman's own|caulipower|bird's eye|green giant
    ore ida|cascadian farm|organic valley|trader joe's|whole foods|kroger|safeway|albertsons
    ben and jerry's|haagen dazs|talenti|breyers|edys|dryers|blue bell|tillamook ice cream
    eggo|vans|nature's path|kashi|cascadian farm|organic valley|trader joe's|whole foods
"""

# BAKERY DEPARTMENT
BAKERY_TERMS = r"""
    bread|white bread|wheat bread|whole wheat bread|rye bread|sourdough bread|french bread|italian bread
    baguette|ciabatta|focaccia|pita bread|naan|tortillas|flour tortillas|corn tortillas|wheat tortillas
    rolls|dinner rolls|hamburger buns|hot dog buns|sandwich rolls|kaiser rolls|potato rolls
    bagels|plain bagels|everything bagels|sesame bagels|poppy seed bagels|blueberry bagels|onion bagels
    english muffins|croissants|danish|muffins|blueberry muffins|chocolate chip muffins|banana muffins
    donuts|glazed donuts|chocolate donuts|jelly donuts|boston cream donuts|powdered donuts|old fashioned donuts
    cakes|birthday cake|chocolate cake|vanilla cake|carrot cake|cheesecake|angel food cake|devil's food cake
    cupcakes|chocolate cupcakes|vanilla cupcakes|red velvet cupcakes|funfetti cupcakes
    cookies|chocolate chip cookies|oatmeal cookies|sugar cookies|peanut butter cookies|snickerdoodles
    brownies|chocolate brownies|blondies|cookie bars|rice krispie treats|granola bars
    pies|apple pie|cherry pie|pumpkin pie|pecan pie|lemon meringue pie|key lime pie|chocolate pie
    pastries|eclairs|cannoli|baklava|strudel|turnovers|palmiers|profiteroles
    artisan bread|fresh bread|homemade bread|baked goods|fresh baked|daily bread
    
    # Bakery brands
    wonder|sara lee|pepperidge farm|arnold|thomas|bimbo|entenmann's|hostess|little debbie|drake's
    nature's own|dave's killer bread|ezekiel|sprouted grain|rudy's|la brea|artisan bread
    thomas|bagel thins|bagel chips|everything bagels|plain bagels|blueberry bagels
    hostess|little debbie|drake's|entenmann's|sara lee|pepperidge farm|arnold|thomas
    dunkin donuts|krispy kreme|entenmann's|sara lee|pepperidge farm|arnold|thomas
    betty crocker|pillsbury|duncan hines|jiffy|king arthur|bob's red mill|arrowhead mills
"""

# PANTRY/GROCERY DEPARTMENT
PANTRY_TERMS = r"""
    pasta|spaghetti|penne|rigatoni|fettuccine|linguine|lasagna|macaroni|elbow macaroni|rotini|fusilli
    rice|white rice|brown rice|basmati rice|jasmine rice|wild rice|arborio rice|sushi rice|instant rice
    beans|black beans|pinto beans|kidney beans|garbanzo beans|chickpeas|navy beans|great northern beans
    lentils|red lentils|green lentils|brown lentils|split peas|black eyed peas
    canned goods|canned vegetables|canned tomatoes|tomato sauce|tomato paste|tomato puree|crushed tomatoes
    canned beans|canned corn|canned peas|canned carrots|canned mushrooms|canned artichokes
    canned fruit|canned peaches|canned pears|canned pineapple|canned mandarin oranges|canned fruit cocktail
    canned meat|canned tuna|canned salmon|canned chicken|canned ham|canned corned beef|spam
    soup|canned soup|chicken noodle soup|tomato soup|vegetable soup|beef stew|clam chowder|chili
    broth|chicken broth|beef broth|vegetable broth|stock|chicken stock|beef stock|vegetable stock
    sauces|pasta sauce|marinara sauce|alfredo sauce|pesto|olive oil|vegetable oil|canola oil|coconut oil
    vinegar|white vinegar|apple cider vinegar|balsamic vinegar|red wine vinegar|white wine vinegar
    condiments|ketchup|mustard|mayonnaise|relish|pickles|olives|black olives|green olives|stuffed olives
    salad dressing|ranch dressing|italian dressing|caesar dressing|blue cheese dressing|thousand island
    peanut butter|jelly|jam|preserves|honey|syrup|maple syrup|pancake syrup|chocolate syrup|caramel syrup
    spices|salt|pepper|garlic powder|onion powder|oregano|basil|thyme|rosemary|sage|bay leaves
    cinnamon|nutmeg|ginger|cumin|paprika|chili powder|cayenne pepper|red pepper flakes|black pepper
    flour|all purpose flour|bread flour|cake flour|whole wheat flour|almond flour|coconut flour
    sugar|white sugar|brown sugar|powdered sugar|confectioners sugar|granulated sugar|raw sugar
    baking|baking soda|baking powder|yeast|active dry yeast|instant yeast|vanilla extract|almond extract
    chocolate chips|semi sweet chocolate chips|milk chocolate chips|white chocolate chips|dark chocolate chips
    nuts|peanuts|almonds|walnuts|pecans|cashews|pistachios|macadamia nuts|hazelnuts|pine nuts
    dried fruit|raisins|cranberries|apricots|prunes|dates|figs|dried mango|dried pineapple|dried apples
    cereal|breakfast cereal|corn flakes|rice krispies|cheerios|special k|frosted flakes|lucky charms
    oatmeal|instant oatmeal|steel cut oats|old fashioned oats|quick oats|granola|muesli
    crackers|saltine crackers|ritz crackers|wheat thins|triscuits|cheez its|goldfish|graham crackers
    chips|potato chips|tortilla chips|corn chips|pita chips|pretzels|popcorn|microwave popcorn
    snacks|trail mix|mixed nuts|beef jerky|turkey jerky|pork rinds|sunflower seeds|pumpkin seeds
    candy|chocolate|chocolates|gum|mints|hard candy|soft candy|gummy candy|sour candy|licorice|truffles|chocolate bars|chocolate candy|chocolate truffles
    beverages|juice|orange juice|apple juice|cranberry juice|grape juice|lemonade|limeade|iced tea
    soda|pop|cola|diet coke|coke zero|pepsi|sprite|7up|dr pepper|root beer|ginger ale|club soda|seltzer
    liquid death|sparkling water|flavored water|energy drinks|sports drinks|gatorade|powerade
    water|bottled water|spring water|purified water|distilled water|sparkling water|mineral water
    coffee|ground coffee|coffee beans|instant coffee|decaf coffee|espresso|coffee filters|coffee pods
    tea|black tea|green tea|herbal tea|chamomile tea|peppermint tea|earl grey|english breakfast
    baby food|baby formula|baby cereal|baby food jars|baby snacks|baby wipes|diapers|pull ups
    
    # Pantry/Grocery brands
    barilla|ronzoni|mueller's|san giorgio|de cecco|bertolli|ragu|prego|hunt's|contadina
    campbell's|progresso|amy's|annie's|health valley|organic valley|trader joe's|whole foods
    heinz|hunt's|del monte|libby's|green giant|le sueur|progresso|campbell's|swanson
    kraft|velveeta|philadelphia|land o lakes|sargento|tillamook|cabot|kerrygold|president
    heinz|hunt's|french's|gulden's|grey poupon|plochman's|annie's|organic valley
    kraft|hellmann's|best foods|duke's|miracle whip|kraft real mayo|sir kensington's
    heinz|hunt's|french's|gulden's|grey poupon|plochman's|annie's|organic valley
    smucker's|welch's|polaner|knott's berry farm|bonne maman|st. dalfour|trader joe's
    kraft|jif|skippy|peter pan|smucker's|justin's|peanut butter co|trader joe's
    mccormick|spice islands|badia|penzeys|the spice house|trader joe's|whole foods
    king arthur|bob's red mill|arrowhead mills|pillsbury|gold medal|white lily|trader joe's
    nestle|hershey's|ghirardelli|lindt|godiva|dove|cadbury|mars|snickers|twix|kit kat
    general mills|kellogg's|post|quaker|nature valley|cheerios|special k|frosted flakes
    frito lay|lays|doritos|cheetos|fritos|ruffles|tostitos|sunchips|popchips|kettle
    coca cola|pepsi|dr pepper|sprite|7up|fanta|mountain dew|root beer|ginger ale|coke zero|liquid death
    nestle|dasani|aquafina|evian|fiji|smartwater|voss|essentia|core|lifewtr
    folgers|maxwell house|starbucks|dunkin|peet's|lavazza|illy|green mountain|keurig
    lipton|twinings|bigelow|celestial seasonings|tazo|stash|yogi|traditional medicinals
    gerber|beech nut|earth's best|happy baby|plum organics|sprout|trader joe's
"""

# HEALTH & BEAUTY DEPARTMENT
HEALTH_BEAUTY_TERMS = r"""
    shampoo|conditioner|hair care|hair products|hair spray|hair gel|mousse|hair dye|hair color
    soap|body wash|hand soap|dish soap|laundry detergent|fabric softener|bleach|cleaning supplies
    toothpaste|toothbrush|dental floss|mouthwash|dental care|oral care|dental products
    deodorant|antiperspirant|body spray|cologne|perfume|fragrance|body lotion|hand lotion|face lotion
    makeup|foundation|concealer|powder|blush|eyeshadow|eyeliner|mascara|lipstick|lip gloss|nail polish
    razors|shaving cream|shaving gel|aftershave|shaving supplies|beard trimmer|electric razor
    feminine care|pads|tampons|feminine hygiene|personal care|personal hygiene
    vitamins|supplements|protein powder|meal replacement|nutritional supplements|vitamin c|vitamin d
    medicine|pain reliever|aspirin|ibuprofen|acetaminophen|tylenol|advil|aleve|cold medicine|cough medicine
    allergy medicine|antihistamine|benadryl|claritin|zyrtec|nasal spray|eye drops|contact solution
    first aid|band aids|bandages|gauze|medical tape|antiseptic|hydrogen peroxide|rubbing alcohol
    sunscreen|suntan lotion|bug spray|insect repellent|mosquito repellent
    toilet paper|paper towels|tissues|facial tissues|paper products|disposable products
    
    # Health & Beauty brands
    pantene|head and shoulders|dove|tresemme|herbal essences|aussie|garnier|l'oreal|nexus|paul mitchell
    dove|dial|irish spring|lever 2000|olay|neutrogena|cetaphil|cerave|aveeno|eucerin
    colgate|crest|oral b|sensodyne|arm and hammer|tom's|hello|quip|phillips|reach
    secret|dove|suave|degree|old spice|axe|gillette|speed stick|ban|mitchum
    maybelline|l'oreal|covergirl|revlon|nyx|elf|milani|physicians formula|almay|wet n wild
    gillette|schick|harry's|dollar shave club|bic|venus|dorco|feather|astra|personna
    always|tampax|kotex|playtex|carefree|stayfree|poise|depend|depends|always discreet
    centrum|one a day|nature made|spring valley|vitafusion|smarty pants|olly|ritual|care/of|hims
    tylenol|advil|aleve|aspirin|bayer|excedrin|motrin|ibuprofen|acetaminophen|naproxen
    benadryl|claritin|zyrtec|allegra|flonase|nasacort|afrin|sudafed|mucinex|robitussin
    band aid|curad|nexcare|3m|johnson and johnson|first aid|medical|healthcare
    neutrogena|coppertone|banana boat|hawaiian tropic|aveeno|cerave|eucerin|la roche posay
"""

# HOUSEHOLD/CLEANING DEPARTMENT
HOUSEHOLD_TERMS = r"""
    cleaning supplies|all purpose cleaner|window cleaner|bathroom cleaner|kitchen cleaner|floor cleaner
    dish soap|dish detergent|dishwasher detergent|dishwasher pods|dishwasher tablets
    laundry detergent|fabric softener|dryer sheets|stain remover|bleach|color safe bleach
    laundry|washing|washing machine|dryer|laundry soap|laundry detergent|laundry pods|laundry sheets
    tide|tide pods|tide liquid|tide powder|tide free|tide original|tide spring meadow|tide lavender
    gain|gain pods|gain liquid|gain powder|gain original|gain moonlight breeze
    persil|persil pods|persil liquid|persil powder|persil original
    arm and hammer|arm & hammer|arm and hammer detergent|arm and hammer pods
    all|all detergent|all pods|all liquid|all free|all clear
    cheer|cheer detergent|cheer pods|cheer liquid|cheer bright clean
    era|era detergent|era pods|era liquid|era original
    oxyclean|oxy clean|oxiclean detergent|oxiclean pods|oxiclean liquid
    dawn|dawn ultra|dawn dish soap|dawn liquid|dawn powerwash|dawn platinum
    method|method dish soap|method hand soap|method all purpose|method laundry
    palmolive|palmo olive|palmo olive dish soap|palmo olive liquid
    ajax|ajax dish soap|ajax liquid|ajax powder
    joy|joy dish soap|joy liquid|joy ultra
    cascade|cascade dishwasher|cascade pods|cascade liquid|cascade powder
    finish|finish dishwasher|finish pods|finish liquid|finish powder
    pods|laundry pods|detergent pods|washing pods|cleaning pods
    paper products|toilet paper|paper towels|napkins|facial tissues|paper plates|paper cups|plastic utensils
    trash bags|garbage bags|ziploc bags|plastic wrap|aluminum foil|parchment paper|wax paper
    batteries|aa batteries|aaa batteries|c batteries|d batteries|9v batteries|button batteries
    light bulbs|led bulbs|incandescent bulbs|fluorescent bulbs|light fixtures|lamps|flashlights
    storage|plastic containers|tupperware|storage bins|organizers|hangers|clothes hangers
    kitchen supplies|pots|pans|cooking utensils|spatulas|spoons|forks|knives|cutting boards|measuring cups
    bathroom supplies|shower curtain|bath mat|toilet brush|plunger|bathroom accessories
    home decor|picture frames|vases|candles|candle holders|throw pillows|blankets|towels|bedding
    hardware|tools|screws|nails|hammers|screwdrivers|wrenches|pliers|tape measure|level
    automotive|motor oil|car wash|car wax|windshield washer fluid|antifreeze|car accessories
    garden|plants|seeds|fertilizer|pesticides|garden tools|watering can|garden hose|plant pots
"""

# HARDWARE/HOME IMPROVEMENT DEPARTMENT
HARDWARE_TERMS = r"""
    # Adhesives & Sealants
    glue|adhesive|super glue|gorilla glue|wood glue|craft glue|hot glue|glue gun|glue sticks
    caulk|silicone caulk|acrylic caulk|latex caulk|caulk gun|caulking|sealant|silicone sealant
    foam|spray foam|expanding foam|great stuff|gaps and cracks|foam sealant|insulation foam
    weather stripping|door seal|window seal|draft stopper|insulation|fiberglass insulation
    
    # Hardware & Fasteners
    screws|nails|bolts|nuts|washers|anchors|wall anchors|drywall anchors|toggle bolts
    hinges|door hinges|cabinet hinges|drawer slides|handles|knobs|pulls|locks|deadbolt
    brackets|corner brackets|l brackets|shelf brackets|pipe straps|conduit straps
    
    # Tools
    drill|drill bits|screwdriver|phillips|flathead|allen wrench|hex key|socket set|ratchet
    wrench|adjustable wrench|pipe wrench|pliers|needle nose|wire cutters|strippers
    hammer|mallet|sledgehammer|level|tape measure|square|chalk line|utility knife
    saw|hand saw|circular saw|reciprocating saw|jigsaw|miter saw|table saw|saw blades
    
    # Electrical
    electrical|outlet|switch|light switch|electrical box|junction box|wire|electrical wire
    extension cord|power strip|surge protector|outlet cover|switch plate|ceiling fan
    light fixture|recessed light|track lighting|chandelier|lamp|desk lamp|floor lamp
    
    # Plumbing
    plumbing|pipe|pvc pipe|copper pipe|galvanized pipe|pipe fittings|elbow|tee|coupling
    valve|shutoff valve|ball valve|gate valve|faucet|kitchen faucet|bathroom faucet
    toilet|toilet seat|toilet tank|toilet bowl|sink|bathroom sink|kitchen sink
    shower|shower head|shower curtain|shower rod|bathtub|drain|p trap|drain cleaner
    
    # Paint & Finishing
    paint|interior paint|exterior paint|primer|paint primer|spray paint|chalk paint
    paint brush|roller|paint roller|paint tray|drop cloth|painter's tape|masking tape
    stain|wood stain|deck stain|varnish|polyurethane|shellac|lacquer|wood finish
    
    # Building Materials
    lumber|plywood|osb|mdf|particle board|drywall|sheetrock|drywall screws|joint compound
    mud|spackle|drywall tape|corner bead|studs|2x4|2x6|4x4|pressure treated|cedar
    concrete|cement|mortar|grout|tile|ceramic tile|porcelain tile|stone tile|mosaic
    
    # Home Improvement
    flooring|hardwood|laminate|vinyl|tile flooring|carpet|carpet pad|baseboard|quarter round
    trim|crown molding|chair rail|wainscoting|paneling|beadboard|shiplap
    roofing|shingles|roofing nails|tar paper|roofing cement|flashing|gutters|downspouts
    
    # Storage & Organization
    shelving|wire shelves|closet system|closet organizer|garage organizer|tool storage
    toolbox|tool chest|pegboard|hooks|brackets|shelving brackets|storage bins
    
    # Safety & Security
    smoke detector|carbon monoxide detector|fire extinguisher|security camera|motion sensor
    doorbell|peephole|chain lock|security bar|window locks|door locks
    
    # Outdoor & Garden
    deck|decking|composite decking|pressure treated decking|deck screws|deck stain
    fence|fence posts|fence panels|gate|gate hardware|fence paint|fence stain
    patio|pavers|concrete pavers|stone pavers|patio furniture|umbrella|grill|grill cover
"""

# ELECTRONICS DEPARTMENT
ELECTRONICS_TERMS = r"""
    tv|television|televisions|smart tv|4k tv|hd tv|led tv|lcd tv|plasma tv|tv stand|tv mount
    computer|laptop|desktop|tablet|ipad|kindle|fire tablet|chromebook|macbook|dell|hp|lenovo
    phone|smartphone|iphone|android|samsung|google pixel|phone case|phone charger|phone screen protector
    headphones|earbuds|airpods|bluetooth headphones|wired headphones|gaming headset
    speakers|bluetooth speaker|wireless speaker|sound bar|home theater|surround sound
    gaming|ps5|ps4|xbox|nintendo switch|video games|game controllers|gaming accessories
    camera|digital camera|webcam|security camera|baby monitor|video baby monitor
    accessories|chargers|cables|hdmi cable|usb cable|power cord|extension cord|power strip
    memory cards|sd card|micro sd|usb drive|flash drive|external hard drive|hard drive
    printer|ink|toner|printer paper|scanner|all in one printer|wireless printer
    router|modem|wifi|internet|network|ethernet cable|wifi extender|mesh wifi
    
    # Electronics brands
    samsung|lg|sony|panasonic|sharp|vizio|tcl|hisense|philips|toshiba|jvc|insignia
    apple|iphone|ipad|macbook|imac|mac|macbook pro|macbook air|ipod|apple watch|airpods
    samsung|galaxy|note|s series|a series|tab|galaxy tab|galaxy watch|galaxy buds
    google|pixel|chromebook|google home|nest|chromecast|google wifi|google nest
    dell|hp|lenovo|acer|asus|msi|alienware|razer|gaming laptop|business laptop
    microsoft|surface|xbox|windows|office|microsoft 365|outlook|teams|skype
    nintendo|switch|wii|ds|3ds|game boy|pokemon|mario|zelda|nintendo switch lite
    sony|playstation|ps5|ps4|ps3|ps2|ps vita|dualshock|playstation vr|sony tv
    microsoft|xbox|xbox series x|xbox series s|xbox one|xbox 360|xbox controller
    canon|nikon|sony|fujifilm|gopro|dji|polaroid|instant camera|digital camera
    bose|sony|jbl|beats|sennheiser|audio technica|shure|marshall|harman kardon
    hp|canon|epson|brother|lexmark|kodak|polaroid|instant printer|photo printer
    netgear|linksys|asus|tp link|d link|google wifi|eero|orbi|mesh wifi|router
"""

# CLOTHING DEPARTMENT
CLOTHING_TERMS = r"""
    shirt|t shirt|tshirt|polo shirt|dress shirt|blouse|tank top|tank tops|sweater|hoodie|hoodies
    jacket|coat|winter coat|rain jacket|windbreaker|blazer|cardigan|vest|sweatshirt|sweatshirts
    pants|jeans|khakis|dress pants|slacks|leggings|yoga pants|sweatpants|shorts|capris|joggers
    dress|dresses|sundress|cocktail dress|formal dress|casual dress|maxi dress|mini dress
    skirt|skirts|mini skirt|maxi skirt|pencil skirt|pleated skirt|denim skirt
    underwear|bra|bras|panties|boxers|briefs|undershirt|undershirts|socks|sock|stockings
    shoes|sneakers|tennis shoes|running shoes|athletic shoes|boots|winter boots|rain boots|dress shoes
    sandals|flip flops|slides|loafers|heels|high heels|pumps|stilettos|wedges|platforms
    accessories|hat|hats|cap|caps|baseball cap|beanie|scarf|scarves|gloves|mittens|belt|belts
    jewelry|necklace|necklaces|earrings|ring|rings|bracelet|bracelets|watch|watches
    bag|bags|purse|purses|handbag|handbags|backpack|backpacks|wallet|wallets|duffel bag|duffel bags
    swimwear|swimsuit|swimsuits|bathing suit|bathing suits|bikini|one piece|swim trunks|swim shorts
    sleepwear|pajamas|pjs|nightgown|nightgowns|robe|robes|sleep shirt|sleep shirts
    maternity|maternity clothes|maternity wear|pregnancy clothes|nursing clothes|nursing bras
    kids clothes|children's clothes|baby clothes|infant clothes|toddler clothes|kids shoes|baby shoes
    
    # Clothing brands
    nike|adidas|under armour|puma|reebok|new balance|converse|vans|skechers|asics
    levi's|lee|wrangler|calvin klein|tommy hilfiger|ralph lauren|polo|nautica|lacoste
    gap|old navy|banana republic|j crew|ann taylor|loft|express|forever 21|h&m|zara
    target|walmart|kohls|macy's|nordstrom|bloomingdale's|saks|neiman marcus|barneys
    victoria's secret|pink|lane bryant|torrid|cacique|maidenform|playtex|hanes|fruit of the loom
    converse|vans|skechers|asics|new balance|brooks|saucony|mizuno|hoka|on running
    coach|michael kors|kate spade|dooney and bourke|fossil|guess|calvin klein|ralph lauren
    cartier|rolex|omega|seiko|citizen|timex|fossil|michael kors|kate spade|guess
    carter's|oshkosh|children's place|gap kids|old navy kids|carters|oshkosh bgosh
"""

# SPORTING GOODS DEPARTMENT
SPORTING_GOODS_TERMS = r"""
    bike|bicycle|mountain bike|road bike|kids bike|children's bike|bike helmet|bike accessories
    exercise|treadmill|elliptical|exercise bike|stationary bike|weights|dumbbells|barbells|weight bench
    yoga|yoga mat|yoga blocks|yoga strap|meditation cushion|yoga towel|yoga clothes
    running|running shoes|running clothes|running shorts|running shirt|running jacket|running socks
    swimming|swim goggles|swim cap|swim fins|kickboard|pool noodles|swimming accessories
    team sports|basketball|basketball hoop|basketball shoes|soccer ball|soccer cleats|football|football helmet
    baseball|baseball bat|baseball glove|baseball cap|softball|softball bat|softball glove
    tennis|tennis racket|tennis balls|tennis shoes|tennis clothes|tennis accessories
    golf|golf clubs|golf balls|golf bag|golf shoes|golf clothes|golf accessories
    camping|tent|sleeping bag|camping stove|camping chair|cooler|camping accessories
    fishing|fishing rod|fishing reel|fishing line|fishing hooks|fishing bait|fishing accessories
    hunting|hunting rifle|hunting bow|hunting arrows|hunting clothes|hunting accessories
    outdoor|hiking boots|hiking clothes|backpack|water bottle|compass|binoculars|outdoor accessories
    
    # Sporting Goods brands
    nike|adidas|under armour|puma|reebok|new balance|converse|vans|skechers|asics
    schwinn|trek|giant|cannondale|specialized|raleigh|huffy|kent|diamondback|mongoose
    bowflex|nordictrack|proform|sole|life fitness|precor|matrix|cybex|hammer strength
    lululemon|athleta|nike|adidas|under armour|puma|reebok|new balance|asics|brooks
    yeti|coleman|igloo|ozark trail|stanley|hydro flask|camelbak|nalgene|klean kanteen
    wilson|spalding|nike|adidas|under armour|puma|reebok|new balance|asics|brooks
    rawlings|wilson|easton|louisville slugger|marucci|demarini|mizuno|nike|adidas
    wilson|head|prince|babolat|yonex|dunlop|volkl|nike|adidas|under armour
    callaway|taylormade|ping|titleist|cobra|wilson|adams|bridgestone|nike|adidas
    coleman|ozark trail|kelty|rei|north face|patagonia|columbia|marmot|mountain hardwear
    shimano|daiwa|abu garcia|penn|okuma|berkley|rapala|zoom|strike king|yum
    remington|winchester|browning|mossberg|savage|ruger|glock|smith and wesson|beretta
"""

# TOYS & GAMES DEPARTMENT
TOYS_GAMES_TERMS = r"""
    toys|toy|dolls|doll|barbie|action figures|action figure|stuffed animals|stuffed animal|teddy bear
    building blocks|lego|legos|duplo|mega bloks|construction toys|building sets
    board games|monopoly|scrabble|chess|checkers|connect four|battleship|clue|risk|trivial pursuit
    puzzles|jigsaw puzzle|puzzle|crossword|word search|brain teaser|logic puzzle
    electronic toys|remote control car|rc car|robot|robotic toy|electronic game|video game|gaming console
    outdoor toys|swing set|slide|trampoline|bounce house|water toys|pool toys|sandbox|sand toys
    baby toys|rattle|teething toy|baby book|mobile|play mat|activity center|walker|bouncer
    educational|science kit|chemistry set|microscope|telescope|magnifying glass|educational games
    collectibles|trading cards|pokemon cards|baseball cards|sports cards|collector items|figurines
    
    # Toys & Games brands
    mattel|barbie|hot wheels|fisher price|little people|thomas and friends|matchbox|american girl
    hasbro|monopoly|scrabble|clue|risk|trivial pursuit|battleship|connect four|operation|twister
    lego|duplo|mega bloks|knex|tinkertoys|lincoln logs|erector set|magna tiles|zoob
    melissa and doug|learning resources|educational insights|leapfrog|vtech|fisher price
    nintendo|mario|pokemon|zelda|animal crossing|splatoon|kirby|donkey kong|metroid
    sony|playstation|spider man|god of war|horizon|last of us|uncharted|ratchet and clank
    microsoft|xbox|halo|gears of war|forza|minecraft|sea of thieves|grounded
    pokemon|pokemon cards|pokemon trading cards|pokemon booster pack|pokemon elite trainer box
    funko|pop vinyl|pop figures|funko pop|collectible figures|vinyl figures
    build a bear|american girl|doll|dolls|barbie|bratz|monster high|ever after high
"""

# ARTS & CRAFTS DEPARTMENT
ARTS_CRAFTS_TERMS = r"""
    arts and crafts|crayons|markers|colored pencils|paint|paint brushes|construction paper|glue|scissors
    coloring books|activity books|sticker books|workbooks|educational toys|learning toys
    craft supplies|yarn|fabric|sewing supplies|thread|needles|buttons|zippers|elastic
    scrapbooking|scrapbook|scrapbook paper|stickers|embellishments|die cuts|punches
    jewelry making|beads|wire|jewelry findings|charms|pendants|earring hooks|necklace chains
    painting|canvas|easel|paint palette|acrylic paint|watercolor|oil paint|paint thinner
    drawing|sketchbook|pencils|charcoal|pastels|markers|colored pencils|erasers
    paper crafts|origami|paper folding|card making|greeting cards|invitations|stationery
    model building|model kits|plastic models|wood models|glue|paint|brushes|tools
    party supplies|balloons|streamers|confetti|party hats|birthday candles|party plates|party cups
    gift wrap|wrapping paper|gift bags|ribbon|bows|gift tags|tissue paper|gift boxes
    seasonal crafts|christmas crafts|halloween crafts|easter crafts|valentine crafts
    home decor crafts|picture frames|vases|candles|candle holders|throw pillows|blankets|towels
    
    # Arts & Crafts brands
    crayola|crayons|markers|colored pencils|paint|construction paper|glue|scissors
    elmer's|glue|glue stick|glue gun|hot glue|craft glue|school glue|white glue
    sharpie|markers|permanent markers|highlighters|dry erase markers|paint markers
    prang|crayons|markers|colored pencils|paint|watercolors|tempera paint|acrylic paint
    roseart|crayons|markers|colored pencils|paint|construction paper|craft supplies
    michaels|joann|hobby lobby|ac moore|pat catans|ben franklin|michael's|jo ann
    dritz|sewing|thread|needles|buttons|zippers|elastic|sewing supplies|sewing notions
    singer|brother|janome|husqvarna|viking|pfaff|bernina|sewing machine|embroidery machine
    red heart|lion brand|bernat|caron|patons|yarn|knitting|crochet|wool|acrylic yarn
    mod podge|decoupage|glue|sealer|finish|craft glue|paper mache|collage
    martha stewart|crafts|diy|home decor|party supplies|scrapbooking|paper crafts
"""

# GARDEN CENTER DEPARTMENT
GARDEN_CENTER_TERMS = r"""
    plants|flowers|seeds|soil|fertilizer|pesticides|garden tools|watering can|garden hose|plant pots
    indoor plants|houseplants|succulents|cacti|orchids|bonsai|palm trees|ficus|monstera|pothos
    outdoor plants|annuals|perennials|shrubs|trees|roses|tulips|daffodils|lilies|marigolds
    vegetable plants|tomato plants|pepper plants|herb plants|lettuce|carrots|beans|cucumbers
    garden tools|shovels|rakes|hoes|pruners|shears|garden gloves|kneeling pad|wheelbarrow
    watering|sprinklers|drip irrigation|soaker hoses|watering cans|sprayers|hose nozzles
    soil and amendments|potting soil|garden soil|compost|peat moss|perlite|vermiculite|mulch
    fertilizers|plant food|fertilizer spikes|liquid fertilizer|organic fertilizer|bone meal
    pest control|insecticides|herbicides|weed killer|slug bait|deer repellent|bird netting
    seasonal|christmas trees|pumpkins|poinsettias|easter lilies|mother's day flowers
    outdoor living|patio furniture|grills|umbrellas|garden decor|bird feeders|bird baths
    landscaping|pavers|stones|edging|landscape fabric|weed barrier|decorative rocks
    
    # Pet supplies and pet food (moved to Pet Supplies department)
    # pet food|dog food|cat food|pet treats|dog treats|cat treats|pet supplies|cat litter|dog toys|pet toys|pet care|pet grooming|pet medicine|pet vitamins|pet bedding|pet carriers|pet collars|pet leashes|pet bowls|pet feeders|pet doors|pet gates|pet crates|pet cages|pet aquariums|fish food|bird food|hamster food|rabbit food|ferret food|reptile food|pet shampoo|pet conditioner|pet flea treatment|pet dewormer|pet supplements|pet dental care|pet nail clippers|pet brushes|pet combs|pet carriers|pet travel|pet training|pet behavior|pet health|pet wellness|pet nutrition|pet diet|pet weight management|pet senior care|pet puppy care|pet kitten care
    
    # Pet food brands (moved to Pet Supplies department)
    # purina|iams|science diet|royal canin|blue buffalo|wellness|merrick|taste of the wild|nutro|natural balance|canidae|orijen|acana|fromm|annamaet|solid gold|wellness core|nutro ultra|natural choice|pedigree|alpo|beneful|fancy feast|friskies|9lives|whiskas|meow mix|iams|eukanuba|hill's|nutro|natural balance|canidae|orijen|acana|fromm|annamaet|solid gold|wellness core|nutro ultra|natural choice|pedigree|alpo|beneful|fancy feast|friskies|9lives|whiskas|meow mix
    
    # Garden Center brands
    miracle gro|scotts|ortho|roundup|bayer|spectracide|sevin|daconil|fertilome|bonide
    burpee|ferry morse|park seed|johnny's selected seeds|botanical interests|rennie's garden
    espoma|jobe's|alaska|foxfarm|general hydroponics|advanced nutrients|botanicare
    fiskars|corona|ames|true temper|bully tools|radius garden|de walt|milwaukee|ryobi
    orbit|melnor|dramm|gilmore|rain bird|hunter|toro|lawn genie|nelson|dramm
    scotts|miracle gro|kellogg|black gold|foxfarm|espoma|jobe's|alaska|fertilome
    ortho|bayer|spectracide|sevin|daconil|fertilome|bonide|safer|garden safe|neem oil
    home depot|lowes|menards|ace hardware|true value|do it best|tractor supply|rural king
    wayfair|amazon|etsy|local nursery|garden center|plant nursery|greenhouse
"""

# BOOKS & MEDIA DEPARTMENT
BOOKS_MEDIA_TERMS = r"""
    books|book|novel|fiction|nonfiction|mystery|romance|thriller|sci fi|fantasy|biography|autobiography
    magazines|magazine|periodical|subscription|news|fashion|home|garden|cooking|health|fitness
    newspapers|newspaper|daily|weekly|local paper|national paper|sunday paper
    dvds|dvd|blu ray|bluray|movies|film|action|comedy|drama|horror|documentary|children's movies
    cds|cd|music|album|pop|rock|country|jazz|classical|hip hop|r&b|soundtrack
    video games|video game|console games|ps5|ps4|xbox|nintendo switch|pc games|steam|digital games
    board games|card games|puzzle games|strategy games|family games|party games|educational games
    educational|textbooks|workbooks|reference books|dictionaries|encyclopedias|atlases|maps
    children's books|picture books|chapter books|young adult|middle grade|bedtime stories
    cookbooks|recipe books|cooking|baking|grilling|slow cooker|instant pot|meal prep
    self help|motivation|business|finance|investing|cooking|travel|history|science|philosophy
"""

# HOME & FURNITURE DEPARTMENT
HOME_FURNITURE_TERMS = r"""
    furniture|living room|sofa|couch|loveseat|recliner|coffee table|end table|tv stand|entertainment center
    bedroom|bed|mattress|box spring|bed frame|headboard|nightstand|dresser|chest|mirror|lamp
    dining room|dining table|dining chairs|buffet|china cabinet|placemats|napkins|tablecloth
    kitchen|kitchen table|kitchen chairs|bar stools|kitchen island|pantry|kitchen cart
    office|desk|office chair|file cabinet|bookshelf|desk lamp|desk organizer|printer stand
    outdoor furniture|patio furniture|patio table|patio chairs|umbrella|hammock|adirondack chairs
    mattresses|memory foam|innerspring|hybrid|pillow top|firm|soft|queen|king|full|twin
    bedding|sheets|pillows|comforter|duvet|blanket|bedspread|quilt|mattress pad|mattress protector
    rugs|area rug|throw rug|runner|doormat|bath mat|kitchen mat|outdoor rug|carpet|carpeting
    curtains|drapes|blinds|shades|valances|curtain rods|curtain rings|tiebacks|window treatments
    home decor|picture frames|vases|candles|candle holders|throw pillows|blankets|towels|bedding
    storage|storage bins|storage boxes|shelving|closet organizers|garage organizers|tool storage
"""

# BABY & KIDS DEPARTMENT
BABY_KIDS_TERMS = r"""
    baby|infant|newborn|toddler|child|children|kids|kid
    baby food|baby formula|baby cereal|baby food jars|baby snacks|baby wipes|diapers|pull ups
    baby clothes|onesies|sleepers|pajamas|socks|shoes|hats|mittens|jackets|pants|shirts
    baby gear|stroller|car seat|high chair|crib|bassinet|playpen|swing|bouncer|walker|jumper
    baby toys|rattle|teething toy|baby book|mobile|play mat|activity center|walker|bouncer
    kids clothing|children's clothes|toddler clothes|kids shoes|baby shoes|kids socks|kids underwear
    kids accessories|backpack|lunch box|water bottle|hair accessories|jewelry|watches|belts
    school supplies|pencils|pens|notebooks|folders|backpack|lunch box|calculator|ruler|scissors
    kids toys|educational toys|learning toys|building toys|art supplies|craft kits|games
    kids books|picture books|chapter books|activity books|coloring books|sticker books
    kids electronics|tablet|headphones|speakers|camera|watch|phone|gaming console|video games
    kids furniture|kids bed|kids desk|kids chair|kids table|bookshelf|toy box|dresser
    kids bedding|kids sheets|kids pillow|kids blanket|kids comforter|kids bedspread
"""

# BEAUTY & PERSONAL CARE DEPARTMENT
BEAUTY_PERSONAL_CARE_TERMS = r"""
    beauty|makeup|cosmetics|foundation|concealer|powder|blush|eyeshadow|eyeliner|mascara|lipstick|lip gloss
    skincare|face wash|moisturizer|serum|toner|mask|sunscreen|anti aging|wrinkle cream|eye cream
    haircare|shampoo|conditioner|hair spray|hair gel|mousse|hair dye|hair color|hair brush|comb
    personal care|deodorant|antiperspirant|body spray|cologne|perfume|fragrance|body lotion|hand lotion
    grooming|razors|shaving cream|shaving gel|aftershave|beard trimmer|electric razor|nail clippers
    beauty tools|makeup brushes|beauty blender|curling iron|straightener|hair dryer|mirror|tweezers
    nail care|nail polish|nail polish remover|nail file|nail clippers|cuticle oil|nail art|manicure
    bath and body|body wash|soap|bath salts|bubble bath|lotion|body scrub|body oil|hand cream
    oral care|toothpaste|toothbrush|dental floss|mouthwash|dental care|oral care|dental products
    feminine care|pads|tampons|feminine hygiene|personal care|personal hygiene|feminine products
    men's grooming|men's razors|men's shaving|men's cologne|men's deodorant|men's hair care
"""

# HEALTH & WELLNESS DEPARTMENT
HEALTH_WELLNESS_TERMS = r"""
    health|wellness|fitness|exercise|workout|gym|training|nutrition|diet|supplements|vitamins
    over the counter|otc|pain reliever|aspirin|ibuprofen|acetaminophen|tylenol|advil|aleve
    cold medicine|cough medicine|decongestant|expectorant|cough suppressant|sore throat|throat lozenges
    allergy medicine|antihistamine|benadryl|claritin|zyrtec|allegra|nasal spray|eye drops
    digestive health|antacid|tums|pepto bismol|imodium|laxative|probiotic|digestive enzymes
    first aid|band aids|bandages|gauze|medical tape|antiseptic|hydrogen peroxide|rubbing alcohol
    vitamins|vitamin c|vitamin d|vitamin b|multivitamin|calcium|iron|omega 3|fish oil
    supplements|protein powder|meal replacement|nutritional supplements|amino acids|creatine
    fitness equipment|treadmill|elliptical|exercise bike|weights|dumbbells|yoga mat|resistance bands
    health monitoring|thermometer|blood pressure monitor|glucose monitor|fitness tracker|pedometer
    personal care|contact solution|contact lens|hearing aid|hearing aid batteries|reading glasses
    medical devices|diabetic supplies|mobility aids|walkers|canes|crutches|wheelchairs
"""

# AUTOMOTIVE CENTER DEPARTMENT
AUTOMOTIVE_CENTER_TERMS = r"""
    automotive|car|vehicle|auto|automobile|truck|suv|motorcycle|rv|boat
    tires|tire|car tires|truck tires|all season|winter tires|summer tires|tire pressure|tire gauge
    batteries|car battery|truck battery|jump starter|battery charger|battery cables|battery terminal
    motor oil|engine oil|synthetic oil|conventional oil|oil filter|air filter|fuel filter|oil change
    car wash|car wax|car polish|car cleaner|windshield washer fluid|antifreeze|coolant|car detailing
    car accessories|car mats|floor mats|seat covers|steering wheel cover|car phone holder|car charger
    car care|car vacuum|car air freshener|car organizer|car storage|car cover|car alarm
    tools|wrenches|screwdrivers|pliers|hammers|socket set|tool box|work gloves|safety glasses
    automotive fluids|transmission fluid|power steering fluid|brake fluid|clutch fluid|radiator fluid
    car parts|brake pads|brake rotors|spark plugs|air filters|fuel filters|belts|hoses|fuses
    emergency|jumper cables|tire inflator|tire repair kit|emergency kit|first aid kit|flashlight
"""

# MOBILE & WIRELESS DEPARTMENT
MOBILE_WIRELESS_TERMS = r"""
    mobile|wireless|cell phone|smartphone|iphone|android|samsung|google pixel|phone|mobile phone
    tablets|tablet|ipad|kindle|fire tablet|chromebook|laptop|desktop|computer|pc|mac
    phone accessories|phone case|phone charger|phone screen protector|phone holder|phone stand
    phone plans|prepaid phone|pay as you go|monthly plan|family plan|unlimited data|texting|calling
    mobile services|phone activation|phone upgrade|phone repair|phone insurance|phone warranty
    chargers|cables|usb cable|lightning cable|wireless charger|car charger|wall charger|portable charger
    headphones|earbuds|airpods|bluetooth headphones|wired headphones|gaming headset|earphones
    mobile data|hotspot|mobile wifi|data plan|unlimited|prepaid|postpaid|family plan
    phone features|camera|gps|bluetooth|wifi|5g|4g|lte|mobile internet|mobile apps
    phone brands|apple|samsung|google|lg|motorola|nokia|oneplus|xiaomi|huawei|sony
"""

# AUTOMOTIVE DEPARTMENT
AUTOMOTIVE_TERMS = r"""
    motor oil|engine oil|synthetic oil|conventional oil|oil filter|air filter|fuel filter
    car wash|car wax|car polish|car cleaner|windshield washer fluid|antifreeze|coolant
    car battery|jumper cables|battery charger|tire pressure gauge|tire inflator|tire repair kit
    windshield wipers|wiper blades|headlight bulbs|tail light bulbs|brake pads|brake fluid
    car accessories|car mats|floor mats|seat covers|steering wheel cover|car phone holder
    car charger|phone charger|usb charger|car adapter|car stereo|speakers|subwoofer
    car care|car detailing|car vacuum|car air freshener|car organizer|car storage
    tools|wrenches|screwdrivers|pliers|hammers|socket set|tool box|work gloves|safety glasses
    automotive fluids|transmission fluid|power steering fluid|brake fluid|clutch fluid
"""

# PHARMACY DEPARTMENT - Prescription and behind-counter items only
PHARMACY_TERMS = r"""
    prescription|prescription medication|prescription drugs|pharmacy|pharmacist|rx|medication|medicine|drug|drugs
    
    # Diabetes supplies (behind counter or require consultation)
    insulin|insulin needles|diabetic needles|syringes|needles|medical needles|injection needles|pen needles
    insulin pen|insulin pump|diabetes pump|insulin pump supplies|diabetes pump supplies
    lancets|test strips|glucose test strips|diabetes test strips|blood glucose strips|sugar test strips|diabetic lancets
    glucose monitor|blood glucose monitor|glucometer|diabetes monitor|sugar monitor|glucose meter
    continuous glucose monitor|cgm|freestyle libre|dexcom|guardian|medtronic|tandem|omnipod
    diabetes supplies|diabetic supplies|diabetes care|diabetic care|diabetes management|blood glucose|blood sugar
    
    # Prescription medications (major brands)
    insulin|humalog|novolog|lantus|levemir|tresiba|basaglar|toujeo|afrezza|fiasp|ryzodeg
    metformin|glipizide|glimepiride|pioglitazone|sitagliptin|saxagliptin|linagliptin|dapagliflozin
    lisinopril|amlodipine|losartan|metoprolol|atenolol|propranolol|carvedilol|bisoprolol
    atorvastatin|simvastatin|rosuvastatin|pravastatin|fluvastatin|lovastatin
    omeprazole|pantoprazole|esomeprazole|lansoprazole|rabeprazole|dexlansoprazole
    albuterol|ventolin|proair|proventil|flovent|advair|symbicort|breo|dulera|asmanex
    montelukast|singulair|zafirlukast|accolate|zyflo|theophylline|theo|uniphyl
    cetirizine|zyrtec|levocetirizine|xyzal|fexofenadine|allegra|loratadine|claritin|desloratadine|clarinex
    diphenhydramine|benadryl|chlorpheniramine|chlor trimeton|brompheniramine|dimetapp
    pseudoephedrine|sudafed|phenylephrine|neosynephrine|oxymetazoline|afrin|nasal spray
    guaifenesin|mucinex|robitussin|dextromethorphan|delsym|codeine|hydrocodone|oxycodone|morphine
    ibuprofen|advil|motrin|naproxen|aleve|naprosyn|diclofenac|voltaren|celecoxib|celebrex
    acetaminophen|tylenol|paracetamol|aspirin|bayer|ecotrin|enteric coated aspirin
    tums|rolaids|pepto bismol|bismuth|imodium|loperamide|kaopectate|attapulgite
    miralax|polyethylene glycol|metamucil|psyllium|fiber|fiber supplement|laxative|stool softener
    prilosec|nexium|prevacid|protonix|aciphex|dexilant|tagamet|cimetidine|zantac|ranitidine|pepcid|famotidine
    pepto bismol|kaopectate|imodium|loperamide|attapulgite|bismuth|antidiarrheal
    tums|rolaids|calcium carbonate|magnesium hydroxide|mylanta|maalox|gaviscon|antacid
    miralax|metamucil|citrucel|benefiber|fiber supplement|psyllium|polyethylene glycol
    dulcolax|senna|bisacodyl|glycerin suppository|fleet enema|laxative|stool softener
    colace|docusate|surfak|stool softener|laxative
    centrum|one a day|vitamin|multivitamin|vitamin c|vitamin d|vitamin b|calcium|iron|zinc|magnesium
    fish oil|omega 3|flaxseed oil|evening primrose oil|borage oil|black cohosh|echinacea|garlic|ginger
    glucosamine|chondroitin|msm|hyaluronic acid|collagen|biotin|coenzyme q10|coq10|melatonin|valerian
    protein powder|whey protein|casein protein|soy protein|pea protein|rice protein|hemp protein
    creatine|bcaa|amino acids|glutamine|arginine|citrulline|beta alanine|taurine|carnitine
    meal replacement|ensure|boost|glucerna|diabetisource|resource|jevity|osmolite|peptamen
    ensure plus|boost plus|glucerna hunger smart|diabetisource ac|resource 2.0|jevity 1.2|osmolite 1.2
    pedialyte|vitamin water|smartwater|essentia|core|bodyarmor|bai|monster|red bull
    ensure|boost|glucerna|diabetisource|resource|jevity|osmolite|peptamen|pediasure|nutren|vivonex
    
    # Medical devices requiring pharmacy consultation
    blood pressure monitor|sphygmomanometer|automatic bp monitor|manual bp monitor|wrist bp monitor|arm bp monitor
    medical alert|medical alarm|emergency alert|personal emergency response|medical pendant|medical bracelet
    hearing aid|hearing aids|hearing aid batteries|hearing aid supplies|hearing aid accessories
    contact lenses|contact lens|contact solution|contact lens solution|contact lens cleaner|contact lens case
    reading glasses|magnifying glasses|bifocals|progressive lenses|prescription glasses|eyeglasses
    cpap|cpap machine|cpap mask|cpap supplies|sleep apnea|sleep therapy|bipap|ventilator
    wheelchair|manual wheelchair|power wheelchair|electric wheelchair|wheelchair accessories|wheelchair parts
    walker|medical walker|rolling walker|wheeled walker|walker accessories|walker parts
    cane|walking cane|quad cane|single point cane|adjustable cane|folding cane
    crutches|underarm crutches|forearm crutches|crutch tips|crutch accessories
    mobility aid|mobility device|mobility equipment|assistive device|assistive equipment
    compression socks|compression stockings|medical compression|compression garments|compression sleeves
    catheter|catheter supplies|foley catheter|intermittent catheter|external catheter|catheter accessories
    ostomy|ostomy supplies|colostomy|ileostomy|urostomy|ostomy bag|ostomy pouch|ostomy accessories
    feeding tube|feeding supplies|enteral feeding|tube feeding|feeding pump|feeding bag|feeding accessories
    medical nutrition|enteral nutrition|parenteral nutrition|medical food|therapeutic nutrition
    medical monitor|patient monitor|vital signs monitor|heart monitor|pulse monitor|oxygen monitor
    medical waste|sharps container|biohazard|medical disposal|needle disposal|sharps disposal
    medical gloves|latex gloves|nitrile gloves|surgical gloves|disposable gloves|exam gloves
    face masks|surgical masks|n95 masks|kn95 masks|medical masks|protective masks|respirator|respirators
    medical scissors|surgical scissors|bandage scissors|suture scissors|medical shears
    medical tweezers|surgical tweezers|forceps|medical forceps|surgical forceps|hemostats
    medical clamps|surgical clamps|bulldog clamps|mosquito clamps|kelly clamps|crile clamps
    stethoscope|nurse stethoscope|doctor stethoscope|pediatric stethoscope|cardiology stethoscope
    pulse oximeter|oxygen saturation|spo2 monitor|finger pulse oximeter|pediatric pulse oximeter
    oxygen|oxygen tank|oxygen concentrator|portable oxygen|oxygen therapy|oxygen supplies
    medical heating pad|therapeutic heating pad|electric heating pad|microwave heating pad|chemical heating pad
    medical compression|compression therapy|compression garments|compression sleeves|compression wraps
    medical alarm|medical alert|emergency response|personal emergency|medical pendant|medical bracelet
    medical waste|biohazard|medical disposal|sharps container|needle disposal|medical sharps
"""

# SEASONAL DEPARTMENT
SEASONAL_TERMS = r"""
    christmas|christmas tree|christmas lights|christmas ornaments|christmas decorations|christmas wrapping paper
    halloween|halloween costume|halloween decorations|halloween candy|pumpkin|jack o lantern
    thanksgiving|turkey|stuffing|cranberry sauce|gravy|pumpkin pie|fall decorations|autumn decorations
    easter|easter basket|easter eggs|easter candy|easter decorations|spring decorations
    valentines day|valentine|valentine cards|valentine candy|valentine decorations|romantic gifts
    mothers day|fathers day|birthday|birthday party|birthday decorations|birthday supplies
    graduation|graduation party|graduation decorations|graduation gifts|celebration supplies
    patriotic|fourth of july|independence day|american flag|patriotic decorations|red white blue
    seasonal|spring|summer|fall|autumn|winter|seasonal decorations|holiday decorations
    party supplies|balloons|streamers|confetti|party hats|birthday candles|party plates|party cups
    gift wrap|wrapping paper|gift bags|ribbon|bows|gift tags|tissue paper|gift boxes
"""

# OFFICE & STATIONERY DEPARTMENT
OFFICE_STATIONERY_TERMS = r"""
    paper|printer paper|copy paper|notebook paper|construction paper|cardstock|poster board
    notebooks|spiral notebook|composition notebook|legal pad|sticky notes|post it notes|index cards
    pens|pencils|markers|highlighters|crayons|colored pencils|paint|paint brushes|art supplies
    folders|file folders|binder|binders|organizer|desk organizer|pencil holder|paper clips|staples
    tape|scotch tape|masking tape|duct tape|packing tape|double sided tape|glue|glue stick|white out
    scissors|ruler|protractor|compass|calculator|stapler|hole punch|paper shredder|laminator
    office furniture|desk|chair|office chair|filing cabinet|bookshelf|storage cabinet|drawer organizer
    electronics|printer|scanner|all in one|wireless printer|ink|toner|printer paper|usb drive
    computer accessories|mouse|keyboard|monitor|webcam|headphones|speakers|microphone
    phone accessories|phone charger|phone case|screen protector|bluetooth speaker|wireless charger
"""

# CUSTOMER SERVICE
CUSTOMER_SERVICE_TERMS = r"""
    return|refund|exchange|customer service|help|assistance|complaint|problem|issue|question
    store hours|hours|open|closed|holiday hours|special hours|extended hours
    location|address|directions|map|store locator|find store|nearest store
    order|online order|pickup|curbside pickup|delivery|shipping|track order|order status
    gift card|gift certificate|store credit|loyalty program|rewards|points|membership
    price|price check|sale|clearance|discount|coupon|promotion|deal|special offer
    product|item|merchandise|inventory|stock|availability|out of stock|backorder
    payment|credit card|debit card|cash|check|money order|payment method|billing
    warranty|guarantee|protection plan|extended warranty|service plan|repair|maintenance
"""

# ===== DEPARTMENT MAPPING =====

# Create comprehensive department rules
GROCERY_DEPT_RULES = [
    # Pharmacy - HIGH PRIORITY (medical supplies take precedence)
    (re.compile(rf"\b({PHARMACY_TERMS})\b", re.I), "Pharmacy"),
    
    # Produce
    (re.compile(rf"\b({PRODUCE_TERMS})\b", re.I), "Produce"),
    
    # Dairy
    (re.compile(rf"\b({DAIRY_TERMS})\b", re.I), "Dairy"),
    
    # Meat & Seafood
    (re.compile(rf"\b({MEAT_SEAFOOD_TERMS})\b", re.I), "Meat & Seafood"),
    
    # Frozen
    (re.compile(rf"\b({FROZEN_TERMS})\b", re.I), "Frozen"),
    
    # Bakery
    (re.compile(rf"\b({BAKERY_TERMS})\b", re.I), "Bakery"),
    
    # Pantry/Grocery - More flexible matching for common items
    (re.compile(rf"\b({PANTRY_TERMS})\b", re.I), "Grocery"),
    
    # Health & Beauty
    (re.compile(rf"\b({HEALTH_BEAUTY_TERMS})\b", re.I), "Health & Beauty"),
    
    # Household/Cleaning
    (re.compile(rf"\b({HOUSEHOLD_TERMS})\b", re.I), "Household"),
    
    # Hardware/Home Improvement
    (re.compile(rf"\b({HARDWARE_TERMS})\b", re.I), "Hardware"),
    
    # Arts & Crafts
    (re.compile(rf"\b({ARTS_CRAFTS_TERMS})\b", re.I), "Arts & Crafts"),
    
    # Garden Center
    (re.compile(rf"\b({GARDEN_CENTER_TERMS})\b", re.I), "Garden Center"),
    
    # Books & Media
    (re.compile(rf"\b({BOOKS_MEDIA_TERMS})\b", re.I), "Books & Media"),
    
    # Home & Furniture
    (re.compile(rf"\b({HOME_FURNITURE_TERMS})\b", re.I), "Home & Furniture"),
    
    # Baby & Kids
    (re.compile(rf"\b({BABY_KIDS_TERMS})\b", re.I), "Baby & Kids"),
    
    # Beauty & Personal Care
    (re.compile(rf"\b({BEAUTY_PERSONAL_CARE_TERMS})\b", re.I), "Beauty & Personal Care"),
    
    # Health & Wellness
    (re.compile(rf"\b({HEALTH_WELLNESS_TERMS})\b", re.I), "Health & Wellness"),
    
    # Automotive Center
    (re.compile(rf"\b({AUTOMOTIVE_CENTER_TERMS})\b", re.I), "Automotive Center"),
    
    # Mobile & Wireless
    (re.compile(rf"\b({MOBILE_WIRELESS_TERMS})\b", re.I), "Mobile & Wireless"),
    
    # Electronics
    (re.compile(rf"\b({ELECTRONICS_TERMS})\b", re.I), "Electronics"),
    
    # Clothing
    (re.compile(rf"\b({CLOTHING_TERMS})\b", re.I), "Clothing"),
    
    # Sporting Goods
    (re.compile(rf"\b({SPORTING_GOODS_TERMS})\b", re.I), "Sporting Goods"),
    
    # Toys & Games
    (re.compile(rf"\b({TOYS_GAMES_TERMS})\b", re.I), "Toys & Games"),
    
    # Automotive
    (re.compile(rf"\b({AUTOMOTIVE_TERMS})\b", re.I), "Automotive"),
    
    # Seasonal
    (re.compile(rf"\b({SEASONAL_TERMS})\b", re.I), "Seasonal"),
    
    # Office & Stationery
    (re.compile(rf"\b({OFFICE_STATIONERY_TERMS})\b", re.I), "Office & Stationery"),
    
    # Customer Service
    (re.compile(rf"\b({CUSTOMER_SERVICE_TERMS})\b", re.I), "Customer Service"),
]

# Add additional flexible patterns for common items that might get mangled by ASR
ADDITIONAL_FLEXIBLE_RULES = [
    # Common grocery items with flexible matching
    (re.compile(r"\bchips?\b", re.I), "Grocery"),
    (re.compile(r"\bcrackers?\b", re.I), "Grocery"),
    (re.compile(r"\bsnacks?\b", re.I), "Grocery"),
    (re.compile(r"\bsoda\b", re.I), "Grocery"),
    (re.compile(r"\bpop\b", re.I), "Grocery"),
    (re.compile(r"\bcola\b", re.I), "Grocery"),
    (re.compile(r"\bjuice\b", re.I), "Grocery"),
    (re.compile(r"\bwater\b", re.I), "Grocery"),
    (re.compile(r"\bbread\b", re.I), "Bakery"),
    (re.compile(r"\bmilk\b", re.I), "Dairy"),
    (re.compile(r"\beggs?\b", re.I), "Dairy"),
    (re.compile(r"\bcheese\b", re.I), "Dairy"),
    (re.compile(r"\byogurt\b", re.I), "Dairy"),
    (re.compile(r"\bbutter\b", re.I), "Dairy"),
    (re.compile(r"\bapples?\b", re.I), "Produce"),
    (re.compile(r"\bbananas?\b", re.I), "Produce"),
    (re.compile(r"\btomatoes?\b", re.I), "Produce"),
    (re.compile(r"\bcucumbers?\b", re.I), "Produce"),
    (re.compile(r"\blettuce\b", re.I), "Produce"),
    (re.compile(r"\bchicken\b", re.I), "Meat & Seafood"),
    (re.compile(r"\bbeef\b", re.I), "Meat & Seafood"),
    (re.compile(r"\bbacon\b", re.I), "Meat & Seafood"),
    (re.compile(r"\bfish\b", re.I), "Meat & Seafood"),
    (re.compile(r"\bpasta\b", re.I), "Grocery"),
    (re.compile(r"\brice\b", re.I), "Grocery"),
    (re.compile(r"\bcereal\b", re.I), "Grocery"),
    (re.compile(r"\boatmeal\b", re.I), "Grocery"),
    (re.compile(r"\bpeanut butter\b", re.I), "Grocery"),
    (re.compile(r"\bjelly\b", re.I), "Grocery"),
    (re.compile(r"\bketchup\b", re.I), "Grocery"),
    (re.compile(r"\bmustard\b", re.I), "Grocery"),
    (re.compile(r"\bpaper towels\b", re.I), "Household"),
    (re.compile(r"\btoilet paper\b", re.I), "Household"),
    (re.compile(r"\bdetergent\b", re.I), "Household"),
    (re.compile(r"\blaundry\b", re.I), "Household"),
    (re.compile(r"\bwashing\b", re.I), "Household"),
    (re.compile(r"\bpods\b", re.I), "Household"),
    (re.compile(r"\btide\b", re.I), "Household"),
    (re.compile(r"\bgain\b", re.I), "Household"),
    (re.compile(r"\bpersil\b", re.I), "Household"),
    (re.compile(r"\barm and hammer\b", re.I), "Household"),
    (re.compile(r"\ball detergent\b", re.I), "Household"),
    (re.compile(r"\bcheer\b", re.I), "Household"),
    (re.compile(r"\bera\b", re.I), "Household"),
    (re.compile(r"\boxyclean\b", re.I), "Household"),
    (re.compile(r"\bshampoo\b", re.I), "Health & Beauty"),
    (re.compile(r"\btoothpaste\b", re.I), "Health & Beauty"),
    (re.compile(r"\bdeodorant\b", re.I), "Health & Beauty"),
    (re.compile(r"\bvitamins?\b", re.I), "Health & Beauty"),
    (re.compile(r"\btv\b", re.I), "Electronics"),
    (re.compile(r"\bphone\b", re.I), "Electronics"),
    (re.compile(r"\bcomputer\b", re.I), "Electronics"),
    (re.compile(r"\bshirt\b", re.I), "Clothing"),
    (re.compile(r"\bpants\b", re.I), "Clothing"),
    (re.compile(r"\bshoes?\b", re.I), "Clothing"),
    (re.compile(r"\bprescription\b", re.I), "Pharmacy"),
    (re.compile(r"\bmedicine\b", re.I), "Pharmacy"),
    (re.compile(r"\bpain reliever\b", re.I), "Pharmacy"),
    
    # Health & Wellness brands and products
    (re.compile(r"\bairborne\b", re.I), "Pharmacy"),
    (re.compile(r"\bemergen-c\b", re.I), "Pharmacy"),
    (re.compile(r"\bzicam\b", re.I), "Pharmacy"),
    (re.compile(r"\bmucinex\b", re.I), "Pharmacy"),
    (re.compile(r"\bnyquil\b", re.I), "Pharmacy"),
    (re.compile(r"\bdayquil\b", re.I), "Pharmacy"),
    (re.compile(r"\btheraflu\b", re.I), "Pharmacy"),
    (re.compile(r"\bvicks\b", re.I), "Pharmacy"),
    (re.compile(r"\brobitussin\b", re.I), "Pharmacy"),
    (re.compile(r"\bchewables\b", re.I), "Pharmacy"),
    (re.compile(r"\bgummies\b", re.I), "Pharmacy"),
    (re.compile(r"\btablets\b", re.I), "Pharmacy"),
    (re.compile(r"\bcapsules\b", re.I), "Pharmacy"),
    (re.compile(r"\bimmune support\b", re.I), "Pharmacy"),
    (re.compile(r"\bwellness\b", re.I), "Pharmacy"),
    (re.compile(r"\bnatural remedies\b", re.I), "Pharmacy"),
    (re.compile(r"\bherbal\b", re.I), "Pharmacy"),
    (re.compile(r"\bprobiotics\b", re.I), "Pharmacy"),
    (re.compile(r"\bomega\b", re.I), "Pharmacy"),
    (re.compile(r"\bfish oil\b", re.I), "Pharmacy"),
    (re.compile(r"\bcalcium\b", re.I), "Pharmacy"),
    (re.compile(r"\bmagnesium\b", re.I), "Pharmacy"),
    (re.compile(r"\bzinc\b", re.I), "Pharmacy"),
    
    # Hardware items with flexible matching
    (re.compile(r"\bfoam\b", re.I), "Hardware"),
    (re.compile(r"\bspray foam\b", re.I), "Hardware"),
    (re.compile(r"\bexpanding foam\b", re.I), "Hardware"),
    (re.compile(r"\bgreat stuff\b", re.I), "Hardware"),
    (re.compile(r"\bgaps and cracks\b", re.I), "Hardware"),
    (re.compile(r"\bcaulk\b", re.I), "Hardware"),
    (re.compile(r"\bsealant\b", re.I), "Hardware"),
    (re.compile(r"\bglue\b", re.I), "Hardware"),
    (re.compile(r"\badhesive\b", re.I), "Hardware"),
    (re.compile(r"\bscrews?\b", re.I), "Hardware"),
    (re.compile(r"\bnails?\b", re.I), "Hardware"),
    (re.compile(r"\bdrill\b", re.I), "Hardware"),
    (re.compile(r"\bhammer\b", re.I), "Hardware"),
    (re.compile(r"\bscrewdriver\b", re.I), "Hardware"),
    (re.compile(r"\bwrench\b", re.I), "Hardware"),
    (re.compile(r"\bpliers\b", re.I), "Hardware"),
    (re.compile(r"\bpaint\b", re.I), "Hardware"),
    (re.compile(r"\bprimer\b", re.I), "Hardware"),
    (re.compile(r"\bstain\b", re.I), "Hardware"),
    (re.compile(r"\bpipe\b", re.I), "Hardware"),
    (re.compile(r"\bvalve\b", re.I), "Hardware"),
    (re.compile(r"\bfaucet\b", re.I), "Hardware"),
    (re.compile(r"\btoilet\b", re.I), "Hardware"),
    (re.compile(r"\bsink\b", re.I), "Hardware"),
    (re.compile(r"\bwire\b", re.I), "Hardware"),
    (re.compile(r"\boutlet\b", re.I), "Hardware"),
    (re.compile(r"\bswitch\b", re.I), "Hardware"),
    (re.compile(r"\blight fixture\b", re.I), "Hardware"),
    (re.compile(r"\blumber\b", re.I), "Hardware"),
    (re.compile(r"\bdrywall\b", re.I), "Hardware"),
    (re.compile(r"\btile\b", re.I), "Hardware"),
    (re.compile(r"\bflooring\b", re.I), "Hardware"),
    (re.compile(r"\bcarpet\b", re.I), "Hardware"),
    (re.compile(r"\btools?\b", re.I), "Hardware"),
    (re.compile(r"\bhardware\b", re.I), "Hardware"),
    
    # Cleaning brands with flexible matching
    (re.compile(r"\bdawn\b", re.I), "Household"),
    (re.compile(r"\bmethod\b", re.I), "Household"),
    (re.compile(r"\bpalmolive\b", re.I), "Household"),
    (re.compile(r"\bajax\b", re.I), "Household"),
    (re.compile(r"\bjoy\b", re.I), "Household"),
    (re.compile(r"\bcascade\b", re.I), "Household"),
    (re.compile(r"\bfinish\b", re.I), "Household"),
    (re.compile(r"\bdish soap\b", re.I), "Household"),
    (re.compile(r"\bdishwasher\b", re.I), "Household"),
    
    # Hair care brands and products with flexible matching
    (re.compile(r"\bmanic\s+panic\b", re.I), "Health & Beauty"),
    (re.compile(r"\bhair\s+dye\b", re.I), "Health & Beauty"),
    (re.compile(r"\bhair\s+color\b", re.I), "Health & Beauty"),
    (re.compile(r"\bclairol\b", re.I), "Health & Beauty"),
    (re.compile(r"\bl'oreal\b", re.I), "Health & Beauty"),
    (re.compile(r"\bgarnier\b", re.I), "Health & Beauty"),
    (re.compile(r"\bwella\b", re.I), "Health & Beauty"),
    (re.compile(r"\bion\b", re.I), "Health & Beauty"),
    (re.compile(r"\bartic\s+fox\b", re.I), "Health & Beauty"),
    (re.compile(r"\bspecial\s+effects\b", re.I), "Health & Beauty"),
    (re.compile(r"\bpunky\s+colour\b", re.I), "Health & Beauty"),
    
    # Beverages and sodas with flexible matching
    (re.compile(r"\bsurge\b", re.I), "Grocery"),
    (re.compile(r"\bmountain dew\b", re.I), "Grocery"),
    (re.compile(r"\bcoca cola\b", re.I), "Grocery"),
    (re.compile(r"\bcoke\b", re.I), "Grocery"),
    (re.compile(r"\bpepsi\b", re.I), "Grocery"),
    (re.compile(r"\bsprite\b", re.I), "Grocery"),
    (re.compile(r"\bfanta\b", re.I), "Grocery"),
    (re.compile(r"\bdr pepper\b", re.I), "Grocery"),
    (re.compile(r"\b7up\b", re.I), "Grocery"),
    (re.compile(r"\bsoda\b", re.I), "Grocery"),
    (re.compile(r"\bpop\b", re.I), "Grocery"),
    (re.compile(r"\bsoft drink\b", re.I), "Grocery"),
    (re.compile(r"\benergy drink\b", re.I), "Grocery"),
    (re.compile(r"\bred bull\b", re.I), "Grocery"),
    (re.compile(r"\bmonster\b", re.I), "Grocery"),
    
    # Candy and chocolate items with flexible matching (ensure candy bars -> Grocery)
    (re.compile(r"\bcandy(\s+bar|\s+bars)?\b", re.I), "Grocery"),
    (re.compile(r"\bchocolate(\s+bar|\s+bars)?\b", re.I), "Grocery"),
    (re.compile(r"\bchocolates\b", re.I), "Grocery"),
    (re.compile(r"\btruffles\b", re.I), "Grocery"),
    (re.compile(r"\bgum\b", re.I), "Grocery"),
    (re.compile(r"\bmints\b", re.I), "Grocery"),
    (re.compile(r"\blicorice\b", re.I), "Grocery"),
    (re.compile(r"\blindor\b", re.I), "Grocery"),
    (re.compile(r"\bhershey\b", re.I), "Grocery"),
    (re.compile(r"\bsnickers\b", re.I), "Grocery"),
    (re.compile(r"\btwix\b", re.I), "Grocery"),
    (re.compile(r"\bkit\s*kat\b", re.I), "Grocery"),
    (re.compile(r"\breese(?:'|)s\b", re.I), "Grocery"),
    (re.compile(r"\bm&ms\b", re.I), "Grocery"),
]

# Combine the rules
ALL_GROCERY_DEPT_RULES = GROCERY_DEPT_RULES + ADDITIONAL_FLEXIBLE_RULES

# ===== AMBIGUOUS ITEMS =====
# Items that could be in multiple departments
GROCERY_AMBIGUOUS_ITEMS = {
    # Bakery vs Grocery
    "bread": ["Bakery", "Grocery"],
    "pita": ["Bakery", "Grocery"],
    "pita bread": ["Bakery", "Grocery"],
    "baguette": ["Bakery", "Grocery"],
    "tortillas": ["Bakery", "Grocery"],
    "english muffins": ["Bakery", "Grocery"],
    "bagels": ["Bakery", "Grocery"],
    
    # Deli vs Grocery vs Meat
    "rotisserie chicken": ["Deli", "Grocery", "Meat & Seafood"],
    "deli meat": ["Deli", "Meat & Seafood"],
    "sushi": ["Deli", "Grocery", "Meat & Seafood"],
    "sandwich": ["Deli", "Grocery"],
    "prepared food": ["Deli", "Grocery"],
    
    # Produce vs Grocery
    "dried fruit": ["Produce", "Grocery"],
    "nuts": ["Produce", "Grocery"],
    "seeds": ["Produce", "Grocery"],
    
    # Dairy vs Grocery
    "milk": ["Dairy", "Grocery"],
    "cheese": ["Dairy", "Grocery"],
    "yogurt": ["Dairy", "Grocery"],
    
    # Frozen vs Grocery
    "frozen vegetables": ["Frozen", "Grocery"],
    "frozen fruit": ["Frozen", "Grocery"],
    "frozen meat": ["Frozen", "Meat & Seafood"],
    
    # Health & Beauty vs Pharmacy
    "vitamins": ["Health & Beauty", "Pharmacy"],
    "supplements": ["Health & Beauty", "Pharmacy"],
    "pain reliever": ["Health & Beauty", "Pharmacy"],
    "cold medicine": ["Health & Beauty", "Pharmacy"],
    
    # Household vs Grocery
    "paper towels": ["Household", "Grocery"],
    "toilet paper": ["Household", "Grocery"],
    "cleaning supplies": ["Household", "Grocery"],
    
    # Electronics vs Office
    "printer": ["Electronics", "Office & Stationery"],
    "computer accessories": ["Electronics", "Office & Stationery"],
    
    # Seasonal vs Other Departments
    "christmas decorations": ["Seasonal", "Household"],
    "halloween decorations": ["Seasonal", "Household"],
    "birthday supplies": ["Seasonal", "Party Supplies"],
    
    # Generic terms that need clarification
    "snacks": ["Grocery", "Health & Beauty"],
    "beverages": ["Grocery", "Health & Beauty"],
    "organic": ["Produce", "Grocery", "Health & Beauty"],
    "gluten free": ["Grocery", "Health & Beauty"],
    "vegan": ["Grocery", "Health & Beauty"],
    "plant based": ["Grocery", "Health & Beauty"],
}

# ===== AISLE LOCATIONS =====
# Common aisle locations for popular items
GROCERY_AISLE_INDEX = {
    # Produce (usually front of store)
    "apples": ["Produce section"],
    "bananas": ["Produce section"],
    "lettuce": ["Produce section"],
    "tomatoes": ["Produce section"],
    
    # Dairy (usually back of store)
    "milk": ["Dairy section"],
    "eggs": ["Dairy section"],
    "cheese": ["Dairy section"],
    "yogurt": ["Dairy section"],
    
    # Meat & Seafood (usually back of store)
    "chicken": ["Meat & Seafood section"],
    "beef": ["Meat & Seafood section"],
    "fish": ["Meat & Seafood section"],
    "bacon": ["Meat & Seafood section"],
    
    # Bakery (usually front of store)
    "bread": ["Bakery section"],
    "cookies": ["Bakery section"],
    "cakes": ["Bakery section"],
    "donuts": ["Bakery section"],
    
    # Grocery aisles (numbered)
    "pasta": ["Aisle 3"],
    "rice": ["Aisle 3"],
    "canned goods": ["Aisle 4"],
    "soup": ["Aisle 4"],
    "cereal": ["Aisle 5"],
    "oatmeal": ["Aisle 5"],
    "peanut butter": ["Aisle 6"],
    "jelly": ["Aisle 6"],
    "condiments": ["Aisle 7"],
    "ketchup": ["Aisle 7"],
    "mustard": ["Aisle 7"],
    "paper towels": ["Aisle 8"],
    "toilet paper": ["Aisle 8"],
    "cleaning supplies": ["Aisle 9"],
    "detergent": ["Aisle 9"],
    "snacks": ["Aisle 10"],
    "chips": ["Aisle 10"],
    "crackers": ["Aisle 10"],
    "beverages": ["Aisle 11"],
    "soda": ["Aisle 11"],
    "juice": ["Aisle 11"],
    "water": ["Aisle 11"],
    "baby food": ["Aisle 12"],
    "diapers": ["Aisle 12"],
    "pet food": ["Pet Supplies department"],
    "dog food": ["Pet Supplies department"],
    "cat food": ["Pet Supplies department"],
    
    # Health & Beauty
    "shampoo": ["Health & Beauty section"],
    "toothpaste": ["Health & Beauty section"],
    "deodorant": ["Health & Beauty section"],
    "vitamins": ["Health & Beauty section"],
    
    # Electronics
    "tv": ["Electronics section"],
    "phone": ["Electronics section"],
    "computer": ["Electronics section"],
    "headphones": ["Electronics section"],
    
    # Clothing
    "shirt": ["Clothing section"],
    "pants": ["Clothing section"],
    "shoes": ["Clothing section"],
    "socks": ["Clothing section"],
    
    # Pharmacy
    "prescription": ["Pharmacy section"],
    "medicine": ["Pharmacy section"],
    "pain reliever": ["Pharmacy section"],
    "cold medicine": ["Pharmacy section"],
}

# ===== HELPER FUNCTIONS =====

def classify_grocery_department(text: str) -> str | None:
    """Classify grocery items to departments using comprehensive rules"""
    t = (text or "").lower().strip()
    
    # ===== CONTEXTUAL KEYWORD SYSTEM =====
    # Use specific contextual keywords to determine product type, not hierarchy
    
    # HOUSEHOLD/CLEANING CONTEXT
    household_context = [
        'dish soap', 'dishwasher', 'dish detergent', 'dish pods',
        'laundry', 'washing', 'dryer', 'fabric softener', 'stain remover',
        'cleaning', 'cleaner', 'bleach', 'all purpose cleaner',
        'paper towels', 'toilet paper', 'trash bags', 'garbage bags'
    ]
    for keyword in household_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Household" and rx.search(t):
                    return dept
    
    # HEALTH & BEAUTY CONTEXT
    beauty_context = [
        'body wash', 'body lotion', 'body spray', 'body scrub',
        'hand soap', 'hand lotion', 'hand cream',
        'face wash', 'face lotion', 'face cream', 'face mask',
        'shampoo', 'conditioner', 'hair care', 'hair products',
        'makeup', 'cosmetics', 'foundation', 'concealer',
        'deodorant', 'antiperspirant', 'cologne', 'perfume'
    ]
    for keyword in beauty_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Health & Beauty" and rx.search(t):
                    return dept
    
    # BAKERY CONTEXT
    bakery_context = [
        'bakery', 'fresh baked', 'artisan bread', 'donuts', 'pastries',
        'croissants', 'danish', 'muffins', 'cakes', 'cupcakes'
    ]
    for keyword in bakery_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Bakery" and rx.search(t):
                    return dept
    
    # DAIRY CONTEXT
    dairy_context = [
        'dairy', 'milk', 'cheese', 'yogurt', 'butter', 'eggs', 'cream',
        'half and half', 'heavy cream', 'sour cream'
    ]
    for keyword in dairy_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Dairy" and rx.search(t):
                    return dept
    
    # MEAT & SEAFOOD CONTEXT
    meat_context = [
        'meat', 'seafood', 'chicken', 'beef', 'pork', 'fish',
        'deli meat', 'bacon', 'ham', 'sausage', 'hot dogs'
    ]
    for keyword in meat_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Meat & Seafood" and rx.search(t):
                    return dept
    
    # PRODUCE CONTEXT
    produce_context = [
        'produce', 'fresh', 'organic', 'fruit', 'vegetable', 'herbs',
        'apples', 'bananas', 'tomatoes', 'lettuce', 'carrots'
    ]
    for keyword in produce_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Produce" and rx.search(t):
                    return dept
    
    # PHARMACY CONTEXT
    pharmacy_context = [
        'prescription', 'pharmacy', 'medicine', 'pain reliever', 'cold medicine',
        'allergy medicine', 'vitamins', 'supplements', 'first aid',
        'chewables', 'gummies', 'tablets', 'capsules', 'liquid medicine',
        'immune support', 'wellness', 'health', 'natural remedies',
        'herbal', 'probiotics', 'omega', 'fish oil', 'calcium',
        'magnesium', 'zinc', 'vitamin c', 'vitamin d', 'b12'
    ]
    for keyword in pharmacy_context:
        if keyword in t:
            for rx, dept in ALL_GROCERY_DEPT_RULES:
                if dept == "Pharmacy" and rx.search(t):
                    return dept
    
    # First try: exact phrase matching with word boundaries (prioritize longer matches)
    # Sort rules by pattern length (longer patterns first) to prioritize specific matches
    sorted_rules = sorted(ALL_GROCERY_DEPT_RULES, key=lambda x: len(x[0].pattern), reverse=True)
    for rx, dept in sorted_rules:
        if rx.search(t):
            return dept
    
    # Second try: word-by-word matching (fallback for ASR issues)
    # But only if no longer phrase matches were found
    words = t.split()
    for word in words:
        # Clean the word (remove punctuation, etc.)
        clean_word = re.sub(r'[^\w\s]', '', word).strip()
        if len(clean_word) < 2:  # Skip very short words
            continue
            
        # Check if this word matches any department
        for rx, dept in ALL_GROCERY_DEPT_RULES:
            if rx.search(clean_word):
                return dept
    
    return None

def get_grocery_department_candidates(item: str) -> list[str]:
    """Get possible departments for a grocery item"""
    if not item:
        return []
    
    t = (item or "").lower().strip()
    candidates = []
    
    # Check ambiguous items first
    for key, depts in GROCERY_AMBIGUOUS_ITEMS.items():
        if key in t:
            for dept in depts:
                if dept not in candidates:
                    candidates.append(dept)
    
    # Check rule-based classification
    dept = classify_grocery_department(t)
    if dept and dept not in candidates:
        candidates.append(dept)
    
    # Fallback to Customer Service
    if not candidates:
        candidates.append("Customer Service")
    
    return candidates

def get_grocery_aisle_location(item: str) -> list[str]:
    """Get aisle location for a grocery item"""
    t = (item or "").lower().strip()
    return GROCERY_AISLE_INDEX.get(t, ["Please ask an associate for the exact location"])

# Export the main components
__all__ = [
    'GROCERY_DEPT_RULES',
    'ALL_GROCERY_DEPT_RULES',
    'GROCERY_AMBIGUOUS_ITEMS', 
    'GROCERY_AISLE_INDEX',
    'classify_grocery_department',
    'get_grocery_department_candidates',
    'get_grocery_aisle_location'
]
