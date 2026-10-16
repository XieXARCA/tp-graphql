import grpc
import schedule_pb2 
import schedule_pb2_grpc

def run():

    with grpc.insecure_channel('localhost:3002') as channel:
        stub = schedule_pb2_grpc.ScheduleStub(channel)


        print("------- GET FULL SCHEDULE -------\n")
        schedule = stub.get_full_schedule(schedule_pb2.Empty())
        for screening in schedule :
            print(screening)
        

        print("------- GET SCHEDULE BY DATE -------\n")
        date = schedule_pb2.Date(date = "20151205")
        schedule = stub.get_schedule_bydate(date)
        print(schedule)

        
        print("------- GET SCHEDULE FROM TO -------\n")
        dates = [ schedule_pb2.Date(date = "20151201"),schedule_pb2.Date(date = "20151212" ) ]
        schedule = stub.get_schedule_from_to(iter(dates))
        for screening in schedule:
            print(screening)


        print("------- ADD SCREENINGS -------\n")
        new_screenings = schedule_pb2.Screenings(screenings = 
        [schedule_pb2.Screening(date = "20151205", movies = ["d772504e-bf25-4549-aaed-7f2305783c3a"]),
         schedule_pb2.Screening(date = "20151206", movies = ["70d13436-355b-401b-bb8d-45626c25762b"]  )] )
        schedule = stub.add_screenings(new_screenings)
        print(schedule)

        print("------- CANCEL SCREENINGS -------\n")
        to_cancel = schedule_pb2.Screenings(screenings = 
        [schedule_pb2.Screening(date = "20151205", movies = ["d772504e-bf25-4549-aaed-7f2305783c3a"]),
         schedule_pb2.Screening(date = "20151206", movies = ["70d13436-355b-401b-bb8d-45626c25762b"]  )] )
        schedule = stub.cancel_screenings(to_cancel)
        print(schedule)

        
if __name__ == '__main__':
    run()