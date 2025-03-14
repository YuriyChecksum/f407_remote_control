/*
 * os.h
 *
 *  Created on: May 30, 2024
 *  Author: Maltsev Yuriy
 */
// самописная ОС реального времени с самым минимум функционала
// через перерывание по внутреннему таймеру/счётчику осматриваем список задач в планировщике,
// то что подоспело, выполняем не вытесняющим способом. Не надо делать задачи тяжёлыми!
// можно менять период запуска.

#ifndef INC_OS_H_
#define INC_OS_H_

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"
#include <stdio.h>

//#define _TASKS_N         _SIZE_N(periods)
#define _TASKS_MAX_N     10   // максимум задач

typedef  void (*pTaskTypeDef)();   /*!< pointer to a Task specific function */

typedef struct {
	pTaskTypeDef task;		// указатель на задачу типа typedef  void (*pTaskTypeDef)();
	uint32_t period;		// период запуска
	uint32_t eventstimer;	// сравниваем с HAL_GetTick()
	uint8_t pause;			// 0 - run, 1 - on pause
	uint8_t n;				// номер задачи в пуле
} TaskInitTypeDef;

//void OS_create(void);
void OS_init(void);
void OS_loop(void);
TaskInitTypeDef* taskAdd(pTaskTypeDef, uint32_t);

// при расположении в "os.h" выдаёт ошибки множестенного определения tasks и cntTasks
//TaskInitTypeDef tasks[_TASKS_MAX_N] = {0};  // рзервируем в памяти структуры описывающие задачи
//uint8_t cntTasks = 0; // текущий счётчик задач

#ifdef __cplusplus
}
#endif

#endif /* INC_OS_H_ */
