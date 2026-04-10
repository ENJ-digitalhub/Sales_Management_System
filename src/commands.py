from src import database

class Commands:
	
	def __init__(self, user=None):
		self.user = user
		self.db = database.Database()
		self.command=""
		self.commandList=[]
		self.mainCommands=("users", "product", "sale", "purchase")
		self.typeCommands={"add":self.addExecutor,\
								"remove":self.removeExecutor}#,\
								# "modify":self.modifyExecutor,\
								# "show":self.showExecutor,\
								# "total":self.totalExecutor, \
								# "search":self.searchExecutor}
	
	def commandParser(self,command):
		self.command= command
		return self.command.split(" ")
	
	def isValid(self,commandList):
		self.commandList=commandList
		while len(self.commandList) != 7:
			self.commandList.append("")
		if self.commandList[0] in self.mainCommands and \
		self.commandList[1] in self.typeCommands.keys():
			print("Valid Command")
			self.typeCommands[self.commandList[1]](self.commandList)
		else:
			print("Invalid Command")
		pass	
	
	def executeCommand(self,command):
		self.command=command
		self.isValid(self.commandParser(self.command))
	
	def addExecutor(self,commandList):
		self.commandList=commandList
		print("adding...")
		#transactions
		sql = f"""
			INSERT INTO transactions (amount, type, status)
			VALUES (?,?,?)
			"""
		params = (self.commandList[2],self.commandList[0], "completed")
		#product
		sql2 = f"""
			INSERT INTO {self.commandList[0]} (name, price, quantity)
			VALUES (?,?,?)

			ON CONFLICT (name) DO UPDATE SET
			name = excluded.name,
			price = excluded.price,
			quantity = quantity + excluded.quantity;
			"""
		params2 = (self.commandList[4], self.commandList[2], self.commandList[3])
		#user
		sql3 = f"""
			INSERT INTO {self.commandList[0]} (first_name, last_name, username, password)
			VALUES (?,?,?,?)

			ON CONFLICT (username) DO UPDATE SET
			first_name = excluded.first_name,
			last_name = excluded.last_name,
			username = excluded.username;
			"""
		params3 = (self.commandList[2], self.commandList[3], self.commandList[4], self.commandList[5])
		try:
			print(self.commandList[0])
			if self.commandList[0] == "users":
				print(sql3, params3)
				self.db.run(sql3, params3)
			elif self.commandList[0] == "product":
				print(sql2, params2)
				self.db.run(sql2, params2)
			else:
				print(sql, params)
				self.db.run(sql, params)
		except Exception as e:
			print(e)
		finally:
			if self.commandList[0] == "sale" or self.commandList[0] == "purchase":
				print(self.user)
				foriegn_key_sql = f"""
					UPDATE transactions
					SET product_id = (
						SELECT id 
						FROM product 
						WHERE name = '{self.commandList[3]}'
						LIMIT 1
					)
					WHERE EXISTS (
						SELECT 1
						FROM product 
						WHERE name = '{self.commandList[3]}'
					);
				"""
				foriegn_key_sql2 = f"""
					UPDATE transactions
					SET user_id = (
						SELECT id 
						FROM users 
						WHERE username = '{self.user}'
						LIMIT 1
					)
					WHERE EXISTS (
						SELECT 1
						FROM users 
						WHERE username = '{self.user}'
					);
				"""
				self.db.run(foriegn_key_sql)
				self.db.run(foriegn_key_sql2)
			else:
				pass
	
	def removeExecutor(self,commandList):
		self.commandList=commandList
		print("removing...")

		sql = f"""
			DELETE FROM {self.commandList[0]} 
			WHERE id = (?)
			"""
		params = (self.commandList[2],)
		try:
			int(self.commandList[2])
			self.db.run(sql,params)
		except Exception as e:
			print(e)
	
	# def modifyExecutor(self,commandList):
	# 	self.commandList=commandList
	# 	print("modifying...")
	# 	sql = f"""
	# 		UPDATE {self.commandList[0]}
	# 		SET amount = ?,label = ?
	# 		WHERE id = ?
	# 		"""
	# 	params = (self.commandList[3],self.commandList[4], self.commandList[5],self.commandList[6], self.commandList[2],)
	# 	sql2 = f"""
	# 		UPDATE {self.commandList[0]}
	# 		SET amount = ?
	# 		WHERE id = ?
	# 		"""
	# 	params2 = (self.commandList[3],self.commandList[2],)
	# 	try:
	# 		int(self.commandList[2])
	# 		self.db.run(sql,params)
	# 	except sqlite3.OperationalError:
	# 		try:
	# 			int(self.commandList[2])
	# 			self.db.run(sql2,params2)
	# 		except Exception as e:
	# 			print(e)
	
	# def showExecutor(self,commandList):
	# 	self.commandList=commandList
	# 	print("showing...")
	# 	sql = f"""
	# 		SELECT * FROM {self.commandList[0]}
	# 		"""
	# 	try:
	# 		records = self.db.query(sql)
	# 		for record in records:
	# 			print(record)
	# 		if len(records) == 0:
	# 			print("(No records found...)")
	# 	except Exception as e:
	# 		print(e)
	
	# def totalExecutor(self,commandList):
	# 	print("totaling...")
	# 	sql = f"""
	# 		SELECT SUM(amount) FROM {self.commandList[0]}
	# 		"""
	# 	sql2 = f"""
	# 		SELECT SUM(amount) FROM {self.commandList[0]}
	# 		WHERE SUBSTR (created_at, 1, LENGTH(?)) = (?)
	# 		"""
	# 	sql3 = f"""
	# 		SELECT SUM(amount) FROM {self.commandList[0]}
	# 		WHERE SUBSTR (record_date, 1, LENGTH(?)) = (?)
	# 		"""
	# 	try:
	# 		if self.commandList[2]=="":
	# 			records = self.db.query(sql)
	# 			for record in records:
	# 				print(record)
	# 		else:
	# 			try:
	# 				if self.commandList[0] != "user":
	# 					records = self.db.query(sql2, (self.commandList[2],self.commandList[2],))
	# 					for record in records:
	# 						print(record)
	# 				else:
	# 					records = self.db.query(sql3, (self.commandList[2],self.commandList[2],))
	# 					for record in records:
	# 						print(record)
	# 			except Exception as e:
	# 				print(e)
	# 	except Exception as e:
	# 				print(e)
	
	# def statusExecutor(self, date= datetime.now().strftime("%Y-%m-%d")):
	# 	print("calculating...")
	# 	sql = f"""
	# 		SELECT ((SELECT SUM(amount) FROM user WHERE SUBSTR (record_date, 1, LENGTH(?)) = (?))+
	# 		(SELECT COALESCE(SUM(amount), 0)  FROM income WHERE SUBSTR (created_at, 1, LENGTH(?)) = (?)))-
	# 		((SELECT COALESCE(SUM(amount), 0)  FROM expenses WHERE SUBSTR (created_at, 1, LENGTH(?)) = (?))+
	# 		(SELECT COALESCE(SUM(amount), 0)  FROM savings WHERE SUBSTR (created_at, 1, LENGTH(?)) = (?))) As status
	# 		"""
	# 	try:
	# 		records = self.db.query(sql, (date, date, date, date, date, date, date, date, ))
	# 		for record in records:
	# 			print(record)
	# 	except Exception as e:
	# 		print(e)		
	
	# def searchExecutor(self, commandList):
	# 	self.commandList=commandList
	# 	print("searching...")
	# 	sql = f"""
	# 		SELECT * FROM {self.commandList[0]}
	# 		WHERE label LIKE (?)
	# 		"""
	# 	try:
	# 		records = self.db.query(sql, (f"%{self.commandList[2]}%",))
	# 		i=0
	# 		for record in records:
	# 			print(record)
	# 			i+=1
	# 		if i == 0:
	# 			print("(No records found...)")
	# 		elif i == 1:
	# 			print(f"\n{i} record found...")
	# 		else:
	# 			print(f"\n{i} records found...")
	# 	except Exception as e:
	# 		print(e)
	
	"""
	
	def historyExecutor(commandList):
	
	
	def previousExecutor(commandList):
	
	
	def nextExecutor(commandList):
	"""
