"""
frd_calculator takes a recipe and calculates the cost of the recipe based on the bulk price of the ingredients.
"""

import pint
from fractions import Fraction
from pint.errors import DimensionalityError
from num2words import num2words
import sys

class Cost:
    def __init__(self, money, quantity, measure):
        self.money = money
        self.quantity = quantity
        self.measure = measure

class Ingredient:
    def __init__(self, quantity, measure, thing):
        self.quantity = quantity
        self.measure = measure
        self.thing = thing
        self.cost = None  # The cost for the large unit of this
        self.price = None  # The price for just this much; What we're ultimately after

    def __str__(self):
        remainder = ""
        if self.cost:
            remainder += f"\nPurchased for ${self.cost.money} per {self.cost.quantity} {self.cost.measure}"
        if self.price:
            remainder += f"Total price for this ingredient: ${self.price}"
        return f"{self.quantity} {self.measure} of {self.thing}.{remainder}"

class Recipe:
    def __init__(self, name):
        self.name = name
        self.ingredients = []

    def __str__(self):
        return f"{self.name}\n" + "\n".join([str(item) for item in self.ingredients])

def read_recipe():
    print("This is the recipe calculator.")
    print("First you will enter the recipe,")
    print("Then I will ask for the cost of the ingredients.")
    print("When we are done, I will print the cost of the recipe.")
    good_to_go = input("Shall we get started? (y/N)")
    if not good_to_go[0] in ['Y','y']:
        print("OK. Maybe next time.")
        sys.exit(0)
    print("Great! Let's get started. For each ingredient,")
    print("I will ask for the name of it, the quantity,")
    print("and then the unit of measure. For example,")
    print("3 cups of flour would be entered like:")
    print("Ingredient: flour")
    print("Quantity: 3")
    print("Unit of measure: cups")
    print("When you have entered all of the ingredients,")
    print("just type \"done\" for the ingredient name.")
    name = input("What shall we call this recipe? ")
    recipe = Recipe(name)
    print("Great!")
    item_count = 1
    done = False
    while not done:
        item = input(f"What's the name of the {num2words(item_count, to='ordinal_num')} item? (eg: flour): ")
        if item.lower().strip() == "done":
            break
        qty = input(f"Great. Now, what's the quantity (only) of {item}? ")
        if '/' in qty:
            qty = float(sum(Fraction(s) for s in qty.split()))
        else:
            qty = float(qty)
        measure = input(f"OK, and the unit of measure? We have {qty} WHATs of {item}? ")
        ingredient = Ingredient(qty, measure, item)
        print(f"Fantastic. I've added {ingredient} to the recipe.")
        recipe.ingredients.append(ingredient)
        item_count += 1
    print("All done. Here's the recipe:")
    print(recipe)
    return recipe

def add_costs(recipe):
    print(f"Now that we have the recipe \"{recipe.name}\"")
    print("we need to figure out the costs.")
    print("For each of the items in the recipe,")
    print("We'll ask how much you paid for how much of it.")
    print("For example, if 5 pounds of flour cost $2.19,")
    print("We'd put 2.19 for the price, 5 for the quantity, and pounds for the unit")
    for item in recipe.ingredients:
        price = float(input(f"How much did you pay for {item.thing}? $"))
        qty = input(f"And what's the quantity of {item.thing} you get for ${price:.2f}? ")
        if '/' in qty:
            qty = float(sum(Fraction(s) for s in qty.split()))
        else:
            qty = float(qty)
        measure = input(f"Finally, you get {qty} WHATs of {item.thing} for ${price:.2f}? ")
        item.cost = Cost(float(price), float(qty), measure)
    print("Great! Now we're done collecting information.")
    print("Give me a moment to calculate your actual price for this recipe...")


def convert_mass_to_volume(cost, rate):
    """
    Manage the unfortunate need to convert items purchased in mass to consumed in volume.
    :param cost: a "Cost" object of an item
    :param rate: The rate in "cups per pound"
    :return: None. The 'cost' item is changed in memory
    """
    ureg = pint.UnitRegistry()
    orig = cost.quantity * ureg[cost.measure]
    orig_in_lbs = orig.to('pounds')
    qty_in_pounds = orig_in_lbs.magnitude
    cups = qty_in_pounds * rate  # rate in cups/pound
    cost.quantity = cups
    cost.measure = "cups"

def check_special_cases(item):
    """
    Often things are sold by _weight_ but put into recipes by _volume_.
    This function tries to take care of common cases of that.
    :param item: An Ingredient
    :return: That same Ingredient, with the "cost" changed to a volume.
    """
    ureg = pint.UnitRegistry()
    # Only bother if the cost dimensionality is mass and the item dimensionality is not
    if ureg[item.cost.measure].dimensionality == ureg.lbs.dimensionality \
            and not ureg[item.measure].dimensionality == ureg.lbs.dimensionality:
        # Set default conversion rate:
        conversion_rate = 2.0  # pounds per cup
        comparison_name = item.thing.lower().strip()
        if "flour" in comparison_name:
            conversion_rate = 3.33
        elif "butter" == comparison_name:
            conversion_rate = 2.0
        elif "brown sugar" in comparison_name:
            conversion_rate = 2.25
        elif "sugar" in comparison_name:
            conversion_rate = 2.0
        elif "cocoa" in comparison_name:
            conversion_rate = 3.55
        # TODO: ADD MORE ITEMS HERE AS YOU LEARN THEM
        convert_mass_to_volume(item.cost, conversion_rate)

    return item


def calculate_recipe_prices(recipe):
    ureg = pint.UnitRegistry()
    for item in recipe.ingredients:
        item = check_special_cases(item)
        bulk = item.cost.quantity * ureg[item.cost.measure]
        try:
            smaller = bulk.to(item.measure)
        except DimensionalityError as dm:
            print(dm)
            continue
        used_fraction = item.quantity / smaller.magnitude
        item.price = used_fraction * item.cost.money


def print_recipe_costs(recipe):
    total = 0
    print(f"Costs for recipe {recipe.name}:")
    for ingredient in recipe.ingredients:
        if ingredient.price:
            print(f"{ingredient.thing}: ${ingredient.price:.2f}")
            total += ingredient.price
        else:
            print(f"Don't have price for {ingredient.thing}")
    print(f"Total: ${total:.2f}")

if __name__ == "__main__":
    recipe = read_recipe()
    add_costs(recipe)
    calculate_recipe_prices(recipe)
    print_recipe_costs(recipe)

