/*
 * os.c
 *
 *  Created on: May 30, 2024
 *  Author: Maltsev Yuriy
 */

#include "os.h"


// при расположении в "os.h" выдаёт ошибки множестенного определения tasks и cntTasks
TaskInitTypeDef tasks[_TASKS_MAX_N] = {0};  // рзервируем в памяти структуры описывающие задачи
uint8_t cntTasks = 0; // текущий счётчик задач

// виртуальный метод, нужно переопределить если нужна
//__attribute__((weak)) void OS_init() { }

/*------- manager --------*/

/* create tasks */
/*void OS_create() {
	taskAdd(&task1, 30000);
	taskAdd(&task2_led, 250);
	taskAdd(&task3_KB, 20);
	taskAdd(&task4_uartRx, 5);

	OS_init(); // init tasks

	OS_loop(); // цикл менеджера задач
}*/

TaskInitTypeDef* taskAdd(pTaskTypeDef pTask, uint32_t period) {
	if ((pTask == NULL) || (cntTasks >= _TASKS_MAX_N)) {
		printf("Err add task\r\n");
		Error_Handler();
		return NULL; }
	TaskInitTypeDef *tsk = &tasks[cntTasks];
	//TaskInitTypeDef tsk = {0};
	tsk->task = pTask;
	tsk->n = cntTasks;
	tsk->period = period;
	tsk->eventstimer = period; // возможно надо заполнить иным значением
	tsk->pause = 0;
	//tasks[cntTasks++] = tsk;
	cntTasks++;
	return tsk;
}

// самописная ОС реального времени с самым минимум функционала
// через перерывание по внутреннему таймеру/счётчику осматриваем список задач в планировщике,
// то что подоспело, выполняем не вытесняющим способом. Не надо делать задачи тяжёлыми!
// можно менять период запуска.
// TO DO: нет семафоров, нет удаления задач, нет приостановки на паузу,
// нет имён задач, нет возможности обратиться к планировщику узнать какая
// задача исполняется и сколько до запуска определённой задачи, нет приостановки в сон между ожиданиями,
// в памяти резервируется под описание структур фиксированное количество места равное размер структуры*макс возможное число задач (_TASKS_MAX_N).
void OS_loop() {
	/*uint32_t ticks = HAL_GetTick();
	for (uint8_t i = 0; i < cntTasks; i++) {
		tasks[i].eventstimer = tasks[i].period + ticks;
	}*/

	//OS_init(); // init tasks

	// loop tasks
	while (1) {
		uint32_t ticks = HAL_GetTick();
		for (uint8_t i = 0; i < cntTasks; i++) {
			if (ticks > tasks[i].eventstimer) { //закончилось ожидание для задачи
				tasks[i].eventstimer = tasks[i].period + ticks; // обновляем таймер задачи
				if (tasks[i].pause){
					continue;
				}
				tasks[i].task(); // исполняем задачу
			}
		}
		/* для усложнения тут надо высчитывать сколько до запуска
		 * ближайшей задачи и на это время настроить аппаратный таймер с прерыванием и уйти в сон
		 * HAL_Delay(1);
		 */
	}
}

