class Star:
    no_star = 'No Star'
    black_star = '★'
    white_star = '☆'

    def __init__(self, star_text: str):
        if star_text in (Star.black_star, Star.white_star, ' ', '', Star.no_star):
            if star_text in (' ', ''):
                star_text = Star.no_star
            self.star_text = star_text
        else:
            self.star_text = 'Error with star'

    @classmethod
    def white(cls):
        return Star(Star.white_star)

    @classmethod
    def black(cls):
        return Star(Star.black_star)

    @classmethod
    def none(cls):
        return Star(Star.no_star)

    @property
    def is_black(self):
        if self.star_text == Star.black_star:
            return True
        return False

    @property
    def is_white(self):
        if self.star_text == Star.white_star:
            return True
        return False

    @property
    def is_no_star(self):
        if self.star_text == Star.no_star:
            return True
        return False

    def __str__(self):
        return self.star_text

    def __eq__(self, other):
        return self.star_text == other.star_text

    def next_star(self, days_between_papers: bool = False):
        # if there are no sitting (or printing) days between the two documents
        # being compared  black stars change to white stars and white stars
        # change to no stars. If there are sitting days between the two
        # documents being compared all stars will change to no star.
        if self.is_black and not days_between_papers:
            return Star.white()
        else:
            return Star.none()


BLACK_STAR = Star.black()
WHITE_STAR = Star.white()
NO_STAR = Star.none()
