import numpy as np


class NaiveSolver_plus:
    def __init__(self, dataset, n_bests=1, step_forward=1, skip_step=1):
        self.problems = dataset
        self.total_cost = 0
        self.n_best = n_bests
        self.step_forward = step_forward
        self.cost_operations = None
        self.trans_cost = None
        self.skip_step = skip_step

    def look_forward(self, horizon, start_city=None, cost=0):
        visited_cities = []
        for stage in horizon:
            if start_city is None:
                reverse_probabilities = 1 / self.cost_operations[stage]
                reverse_probabilities /= np.sum(reverse_probabilities)

                city = np.random.choice(
                    np.argsort(self.cost_operations[stage]), p=reverse_probabilities
                )

                visited_cities.append(city)
                cost += self.cost_operations[stage][city]
            else:
                cost_total = self.cost_operations[stage] + self.trans_cost[start_city]
                variants = np.argsort(cost_total)[: self.n_best]

                reverse_probabilities = 1 / cost_total[variants]
                reverse_probabilities /= np.sum(reverse_probabilities)

                city = np.random.choice(variants, p=reverse_probabilities)

                visited_cities.append(city)
                cost += cost_total[city]
        return cost, visited_cities

    def sample_forward(self, horizon, init_city, num):
        rand_walk = [self.look_forward(horizon, init_city) for _ in range(num)]
        return rand_walk

    def solve_suboperaion(self, available_operations):
        """
        Solve problem for one suboperation
        """
        sub_problem_data = []
        city = None
        skip_list = []
        for i, stage in enumerate(available_operations):
            horizon = available_operations[i : i + self.step_forward]

            if len(skip_list) == 0:
                rand_walk = self.sample_forward(horizon, city, 500)
                min_index = np.argmin([item[0] for item in rand_walk])
                skip_list = rand_walk[min_index][1][: self.skip_step]

            if city is None:
                # city = rand_walk[min_index][1][0]
                city = skip_list.pop(0)
                sub_problem_data.append([city, self.cost_operations[stage, city]])
            else:
                # new_city = rand_walk[min_index][1][0]
                new_city = skip_list.pop(0)
                cost_total = self.cost_operations[stage] + self.trans_cost[city]
                city = new_city
                sub_problem_data.append([city, cost_total[city]])

        return np.array(sub_problem_data)[:, 0], np.sum(
            np.array(sub_problem_data)[:, 1]
        )

    def solve_problem(self, num_problem, save_costs=False):
        """
        Solve operation
        """
        n_tasks = self.problems[num_problem]["n_tasks"]
        operation = self.problems[num_problem]["operation"]
        dist = self.problems[num_problem]["dist"]
        time_cost = self.problems[num_problem]["time_cost"]
        op_cost = self.problems[num_problem]["op_cost"]
        productivity = self.problems[num_problem]["productivity"]
        transportation_cost = self.problems[num_problem]["transportation_cost"]

        self.cost_operations = time_cost * op_cost / productivity
        self.trans_cost = dist * transportation_cost

        problem_cost = 0
        problem_path = {}

        for n_sub in range(n_tasks):
            available_operations = np.nonzero(operation[:, n_sub])[0]
            path, cost = self.solve_suboperaion(available_operations)

            problem_cost += cost
            problem_path[f"suboperation_{n_sub}"] = path
        if save_costs:
            self.total_cost += problem_cost
        return {"path": problem_path, "cost": problem_cost}
