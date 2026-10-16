import grpc
import json

import schedule_pb2
import schedule_pb2_grpc

from concurrent import futures

class ScheduleServicer(schedule_pb2_grpc.ScheduleServicer):

    def __init__(self):
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]

    def write(self,schedule):
        with open('{}/data/times.json'.format("."), "w") as wfile:
            json.dump({"schedule": schedule }, wfile)
    
    def remove(self,scheduled):
        with open('{}/data/times.json'.format("."), "w") as wfile:
            self.db.remove(scheduled)


    def dictionary(self,screening):
        return {"date": screening.date, "movies": list(screening.movies)}

    def get_full_schedule (self, request, context) :
        for scheduled in self.db:
            yield schedule_pb2.Screening(date=scheduled["date"], movies=scheduled["movies"])        
        
    def get_schedule_bydate(self, request, context) :
        for scheduled in self.db :
            if scheduled["date"] == request.date : 
                print('Screening found!')
                return schedule_pb2.Screening(date = scheduled["date"], movies = scheduled["movies"])

        return schedule_pb2.Screening(date = "", movies = "" )

    def get_schedule_from_to(self, request_iterator, context):

        i = 0

        From = next(request_iterator)
        to = next(request_iterator)

        schedulingTab = []
        for scheduled in self.db:
            if scheduled["date"] == From.date:
                break
            i += 1

        if len(self.db) - 1 == i:
            return schedule_pb2.Screening(date= "", movies= "") 

        for scheduled in self.db[i:]:
            schedulingTab.append(schedule_pb2.Screening(date= scheduled["date"], movies= scheduled["movies"]))
            if scheduled["date"] == to.date :
                break

        if scheduled["date"] == to.date:
            for scheduling in schedulingTab:
                yield scheduling

    def add_screenings(self, request, context):
        
        for screening in request.screenings:

            inserted= False
            for i , scheduled in enumerate(self.db):
                    
                if screening.date < scheduled["date"]:
                    self.db.insert(i, self.dictionary(screening)) 
                    self.write(self.db)
                    inserted = True

                    break

                elif screening.date == scheduled["date"]: 
                    scheduled["movies"].extend(list(screening.movies))
                    self.write(self.db)
                    inserted = True
                    
                    break

            if not inserted :
                self.db.append({"date":screening.date, "movies" : list(screening.movies)})
                self.write(self.db)   
                    
        return schedule_pb2.Screenings(screenings = self.db)
                    
    def cancel_screenings(self, request, context):
        
        for screening in request.screenings:
            for scheduled in self.db:
                if screening.date == scheduled["date"]: 
                    for movie in list(screening.movies):
                        scheduled["movies"].remove(movie) 

                    if not scheduled["movies"]:
                        self.remove(scheduled)

                    self.write(self.db)

        return schedule_pb2.Screenings(screenings = self.db)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    schedule_pb2_grpc.add_ScheduleServicer_to_server(ScheduleServicer(), server)
    server.add_insecure_port('[::]:3002')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
