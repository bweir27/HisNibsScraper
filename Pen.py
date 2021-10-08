class Pen:
    def __init__(self, brand, name, price, srcUrl, inStock):
        # self.code = code
        self.brand = brand
        # self.series = series
        self.name = name
        # self.color = color
        self.price = price
        # self.img = img
        self.srcUrl = srcUrl
        self.inStock = inStock and True

    def __str__(self):
        return f'{self.brand} {self.name} -- ${self.price} at {self.srcUrl}'


