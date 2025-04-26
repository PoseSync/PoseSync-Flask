class Record:
    def __init__(self, exercise_cnt=0, exercise_name="", exercise_weight=0.0, phone_number=""):
        # 운동 횟수
        self.exercise_cnt = exercise_cnt
        # 운동 이름
        self.exercise_name = exercise_name
        # 운동 무게
        self.exercise_weight = exercise_weight
        # 사용자 전화번호
        self.phone_number = phone_number

    @property
    def exercise_cnt(self):
        return self._exercise_cnt

    @exercise_cnt.setter
    def exercise_cnt(self, exercise_cnt):
        self._exercise_cnt = exercise_cnt

    @property
    def exercise_name(self):
        return self._exercise_name

    @exercise_name.setter
    def exercise_name(self, exercise_name):
        self._exercise_name = exercise_name

    @property
    def exercise_weight(self):
        return self._exercise_weight

    @exercise_weight.setter
    def exercise_weight(self, exercise_weight):
        self._exercise_weight = exercise_weight

    @property
    def phone_number(self):
        return self._phone_number

    @phone_number.setter
    def phone_number(self, phone_number):
        self._phone_number = phone_number
