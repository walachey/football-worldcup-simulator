CPP_FILES := $(wildcard *.cpp) $(wildcard deps/json_spirit/*.cpp)
OBJ_FILES := $(addprefix obj/,$(notdir $(CPP_FILES:.cpp=.o)))
LD_FLAGS := 
CC_FLAGS := -std=c++11 -DNDEBUG -I deps -o3

simulator: $(OBJ_FILES)
	g++ $(LD_FLAGS) -o $@ $^

obj/%.o: %.cpp
	g++ $(CC_FLAGS) -c -o $@ $<

obj/%.o: deps/json_spirit/%.cpp
	g++ $(CC_FLAGS) -c -o $@ $<

#-include $(OBJFILES:.o=.d)
