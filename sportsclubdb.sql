CREATE DATABASE SportsClubDB;
USE SportsClubDB;

CREATE TABLE Member (
    MemberID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Age INT CHECK (Age BETWEEN 10 AND 80),
    Gender CHAR(1) CHECK (Gender IN ('M', 'F')),
    ContactNo VARCHAR(15),
    Email VARCHAR(100) UNIQUE,
    MembershipType VARCHAR(20),
    JoinDate DATE DEFAULT (CURDATE())
);

CREATE TABLE Payment (
    PaymentID INT PRIMARY KEY,
    Amount DECIMAL(10,2) NOT NULL,
    PaymentDate DATE NOT NULL,
    PaymentMode VARCHAR(20),
    MemberID INT,
    CONSTRAINT FK_Payment_Member FOREIGN KEY (MemberID) REFERENCES Member(MemberID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE Coach (
    CoachID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Specialization VARCHAR(100),
    ContactNo VARCHAR(15),
    Email VARCHAR(100) UNIQUE
);

CREATE TABLE Activity (
    ActivityID INT PRIMARY KEY,
    ActivityName VARCHAR(100) NOT NULL,
    Description TEXT,
    CoachID INT,
    CONSTRAINT FK_Activity_Coach FOREIGN KEY (CoachID) REFERENCES Coach(CoachID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TABLE Event (
    EventID INT PRIMARY KEY,
    EventName VARCHAR(100),
    Date DATE,
    Location VARCHAR(100),
    ActivityID INT,
    CONSTRAINT FK_Event_Activity FOREIGN KEY (ActivityID) REFERENCES Activity(ActivityID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

CREATE TABLE Participation (
    ParticipationID INT PRIMARY KEY,
    Result VARCHAR(50),
    MemberID INT,
    EventID INT,
    CONSTRAINT FK_Participation_Member FOREIGN KEY (MemberID) REFERENCES Member(MemberID)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT FK_Participation_Event FOREIGN KEY (EventID) REFERENCES Event(EventID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE Member_Log (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    MemberID INT,
    Action VARCHAR(100),
    LogDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO Member VALUES
(1, 'Alice Johnson', 28, 'F', '9876543210', 'alicej@gmail.com', 'Annual', '2025-01-10'),
(2, 'Bob Smith', 35, 'M', '8765432109', 'bobs@gmail.com', 'Half-Yearly', '2025-02-15'),
(3, 'Charlie Lee', 22, 'M', '7654321098', 'charliel@gmail.com', 'Quarterly', '2025-03-20'),
(4, 'Diana Prince', 30, 'F', '6543210987', 'dianap@gmail.com', 'Annual', '2025-04-25'),
(5, 'Evan Davis', 40, 'M', '5432109876', 'evand@gmail.com', 'Half-Yearly', '2025-05-30');

INSERT INTO Payment VALUES
(1, 500.00, '2025-01-11', 'Credit Card', 1),
(2, 300.00, '2025-02-16', 'Cash', 2),
(3, 150.00, '2025-03-21', 'Debit Card', 3),
(4, 600.00, '2025-04-26', 'UPI', 4),
(5, 350.00, '2025-05-31', 'Net Banking', 5);

INSERT INTO Coach VALUES
(1, 'Coach Morgan', 'Fitness', '9123456789', 'morgan@gmail.com'),
(2, 'Coach Taylor', 'Swimming', '9234567890', 'taylor@gmail.com'),
(3, 'Coach Jordan', 'Tennis', '9345678901', 'jordan@gmail.com');

INSERT INTO Activity VALUES
(1, 'Yoga', 'Flexibility and Mindfulness', 1),
(2, 'Swimming', 'Aquatic Fitness', 2),
(3, 'Tennis', 'Racket Sport', 3),
(4, 'Zumba', 'Dance Aerobics', 1),
(5, 'Gym Workout', 'Strength Training', 1);

INSERT INTO Event VALUES
(1, 'Annual Marathon', '2025-08-15', 'City Park', 5),
(2, 'Swimming Championship', '2025-09-10', 'Aquatic Center', 2),
(3, 'Yoga Workshop', '2025-07-05', 'Health Club', 1),
(4, 'Tennis Open', '2025-10-20', 'Sports Complex', 3),
(5, 'Zumba Fest', '2025-11-25', 'Community Hall', 4);

INSERT INTO Participation VALUES
(1, 'Completed', 1, 1),
(2, 'Winner', 2, 2),
(3, 'Participant', 3, 3),
(4, 'Runner-Up', 4, 4),
(5, 'Participant', 5, 5);


DELIMITER $$
CREATE TRIGGER update_membership_after_payment
AFTER INSERT ON Payment
FOR EACH ROW
BEGIN
    DECLARE total_paid DECIMAL(10,2);
    SELECT SUM(Amount) INTO total_paid FROM Payment WHERE MemberID = NEW.MemberID;

    IF total_paid >= 1000 THEN
        UPDATE Member SET MembershipType = 'Premium' WHERE MemberID = NEW.MemberID;
    ELSEIF total_paid >= 500 THEN
        UPDATE Member SET MembershipType = 'Annual' WHERE MemberID = NEW.MemberID;
    ELSE
        UPDATE Member SET MembershipType = 'Basic' WHERE MemberID = NEW.MemberID;
    END IF;
END$$


CREATE TRIGGER after_member_insert
AFTER INSERT ON Member
FOR EACH ROW
BEGIN
    INSERT INTO Member_Log(MemberID, Action)
    VALUES (NEW.MemberID, 'New Member Added');
END$$


CREATE TRIGGER prevent_coach_delete
BEFORE DELETE ON Coach
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM Activity WHERE CoachID = OLD.CoachID) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete coach assigned to an activity.';
    END IF;
END$$
DELIMITER ;


DELIMITER $$
CREATE PROCEDURE EventParticipationReport(IN event_name VARCHAR(100))
BEGIN
    SELECT E.EventName, M.Name AS MemberName, P.Result
    FROM Participation P
    JOIN Member M ON P.MemberID = M.MemberID
    JOIN Event E ON P.EventID = E.EventID
    WHERE E.EventName = event_name;
END$$


CREATE PROCEDURE GetActivitiesByCoach(IN coach_name VARCHAR(100))
BEGIN
    SELECT A.ActivityID, A.ActivityName, A.Description
    FROM Activity A
    JOIN Coach C ON A.CoachID = C.CoachID
    WHERE C.Name = coach_name;
END$$


CREATE PROCEDURE GetHighPayingMembers(IN min_amount DECIMAL(10,2))
BEGIN
    SELECT M.MemberID, M.Name, P.Amount, P.PaymentDate
    FROM Member M
    JOIN Payment P ON M.MemberID = P.MemberID
    WHERE P.Amount > min_amount;
END$$
DELIMITER ;



DELIMITER $$
CREATE FUNCTION GetParticipationCount(mem_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total INT;
    SELECT COUNT(*) INTO total FROM Participation WHERE MemberID = mem_id;
    RETURN total;
END$$


CREATE FUNCTION GetTotalPayment(mem_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT COALESCE(SUM(Amount), 0) INTO total FROM Payment WHERE MemberID = mem_id;
    RETURN total;
END$$


CREATE FUNCTION IsMemberActive(mem_id INT)
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE active_status BOOLEAN;
    SELECT COUNT(*) > 0 INTO active_status
    FROM Participation P
    JOIN Event E ON P.EventID = E.EventID
    WHERE P.MemberID = mem_id AND E.Date > CURDATE();
    RETURN active_status;
END$$
DELIMITER ;
