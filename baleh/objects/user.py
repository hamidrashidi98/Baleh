class User:
      def __init__(self, id: int, username: str = None, first_name: str = None, last_name: str = None):
          self.id = id
          self.username = username
          self.first_name = first_name
          self.last_name = last_name

      def __str__(self):
          return f"User(id={self.id}, username={self.username}, first_name={self.first_name}, last_name={self.last_name})"