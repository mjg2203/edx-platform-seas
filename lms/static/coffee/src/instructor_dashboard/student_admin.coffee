# Student Admin Section

# imports from other modules.
# wrap in (-> ... apply) to defer evaluation
# such that the value can be defined later than this assignment (file load order).
plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
plantInterval = -> window.InstructorDashboard.util.plantInterval.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
load_IntervalManager = -> window.InstructorDashboard.util.IntervalManager


# wrap window.confirm
# display `msg`
# run `ok` or `cancel` depending on response
confirm_then = ({msg, ok, cancel}) ->
  if window.confirm msg then ok?() else cancel?()

# get jquery element and assert its existance
find_and_assert = ($root, selector) ->
  item = $root.find selector
  if item.length != 1
    console.error "element selection failed for '#{selector}' resulted in length #{item.length}"
    throw "Failed Element Selection"
  else
    item

# render a task list table to the DOM
# `$table_tasks` the $element in which to put the table
# `tasks_data`
create_task_list_table = ($table_tasks, tasks_data) ->
  $table_tasks.empty()

  options =
    enableCellNavigation: true
    enableColumnReorder: false
    autoHeight: true
    rowHeight: 60
    forceFitColumns: true

  columns = [
    id: 'task_type'
    field: 'task_type'
    name: 'Task Type'
  ,
    id: 'requester'
    field: 'requester'
    name: 'Requester'
    width: 30
  ,
    id: 'task_input'
    field: 'task_input'
    name: 'Input'
  ,
    id: 'task_state'
    field: 'task_state'
    name: 'State'
    width: 30
  ,
    id: 'task_id'
    field: 'task_id'
    name: 'Task ID'
    width: 50
  ,
    id: 'created'
    field: 'created'
    name: 'Created'
  ]

  table_data = tasks_data

  $table_placeholder = $ '<div/>', class: 'slickgrid'
  $table_tasks.append $table_placeholder
  grid = new Slick.Grid($table_placeholder, table_data, columns, options)


class StudentAdmin
  constructor: (@$section) ->
    @$section.data 'wrapper', @

    # gather buttons
    # some buttons are optional because they can be flipped by the instructor task feature switch
    # student-specific
    @$field_student_select_progress = find_and_assert @$section, "input[name='student-select-progress']"
    @$field_student_select_grade  = find_and_assert @$section, "input[name='student-select-grade']"
    @$progress_link               = find_and_assert @$section, "a.progress-link"
    @$field_problem_select_single = find_and_assert @$section, "input[name='problem-select-single']"
    @$btn_reset_attempts_single   = find_and_assert @$section, "input[name='reset-attempts-single']"
    @$btn_enroll                  = @$section.find "input[name='enroll']"
    @$btn_unenroll                = @$section.find "input[name='unenroll']"
    @$btn_delete_state_single     = @$section.find "input[name='delete-state-single']"
    @$btn_rescore_problem_single  = @$section.find "input[name='rescore-problem-single']"
    @$btn_task_history_single     = @$section.find "input[name='task-history-single']"
    @$table_task_history_single   = @$section.find ".task-history-single-table"

    # course-specific
    @$field_problem_select_all    = @$section.find "input[name='problem-select-all']"
    @$btn_reset_attempts_all      = @$section.find "input[name='reset-attempts-all']"
    @$btn_rescore_problem_all     = @$section.find "input[name='rescore-problem-all']"
    @$btn_task_history_all        = @$section.find "input[name='task-history-all']"
    @$table_task_history_all      = @$section.find ".task-history-all-table"
    @$table_running_tasks         = @$section.find ".running-tasks-table"

    # response areas
    @$request_response_error_progress = find_and_assert @$section, ".student-specific-container .request-response-error"
    @$request_response_error_grade = find_and_assert @$section, ".student-grade-container .request-response-error"
    @$request_response_error_all    = @$section.find ".course-specific-container .request-response-error"

    # start polling for task list
    # if the list is in the DOM
    if @$table_running_tasks.length > 0
      # reload every 20 seconds.
      TASK_LIST_POLL_INTERVAL = 20000
      @reload_running_tasks_list()
      @task_poller = new (load_IntervalManager()) TASK_LIST_POLL_INTERVAL, =>
        @reload_running_tasks_list()

    # attach click handlers

    # go to student progress page
    @$progress_link.click (e) =>
      e.preventDefault()
      unique_student_identifier = @$field_student_select_progress.val()
      if not unique_student_identifier
        return @$request_response_error_progress.text "Please enter a student email address or username."

      $.ajax
        dataType: 'json'
        url: @$progress_link.data 'endpoint'
        data: unique_student_identifier: unique_student_identifier
        success: @clear_errors_then (data) ->
          window.location = data.progress_url
        error: std_ajax_err => @$request_response_error_progress.text "Error getting student progress url for '#{unique_student_identifier}'."

    # enroll student
    @$btn_enroll.click =>
      send_data =
        action: 'enroll'
        emails: @$field_student_select_progress.val()
        auto_enroll: false

      $.ajax
        dataType: 'json'
        url: @$btn_enroll.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> console.log "student #{send_data.emails} enrolled"
        error: std_ajax_err => @$request_response_error_progress.text "Error enrolling student '#{send_data.emails}'."

    # unenroll student
    @$btn_unenroll.click =>
      send_data =
        action: 'unenroll'
        emails: @$field_student_select_progress.val()

      $.ajax
        dataType: 'json'
        url: @$btn_unenroll.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> console.log "student #{send_data.emails} unenrolled"
        error: std_ajax_err => @$request_response_error_progress.text "Error unenrolling student '#{send_data.emails}'."

    # reset attempts for student on problem
    @$btn_reset_attempts_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text "Please enter a student email address or username."
      if not problem_to_reset
        return @$request_response_error_grade.text "Please enter a problem urlname."
      send_data =
        unique_student_identifier: unique_student_identifier
        problem_to_reset: problem_to_reset
        delete_module: false

      $.ajax
        dataType: 'json'
        url: @$btn_reset_attempts_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> alert "Success! Problem attempts reset for problem '#{problem_to_reset}' and student '#{unique_student_identifier}'."
        error: std_ajax_err => @$request_response_error_grade.text "Error resetting problem attempts for problem '#{problem_to_reset}' and student '#{unique_student_identifier}'."

    # delete state for student on problem
    @$btn_delete_state_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text "Please enter a student email address or username."
      if not problem_to_reset
        return @$request_response_error_grade.text "Please enter a problem urlname."

      if window.confirm "Delete student '#{unique_student_identifier}'s state on problem '#{problem_to_reset}'?"
        send_data =
          unique_student_identifier: unique_student_identifier
          problem_to_reset: problem_to_reset
          delete_module: true

        $.ajax
          dataType: 'json'
          url: @$btn_delete_state_single.data 'endpoint'
          data: send_data
          success: @clear_errors_then -> alert 'Module state successfully deleted.'
          error: std_ajax_err => @$request_response_error_grade.text "Error deleting problem state."
      else
        @clear_errors()

    # start task to rescore problem for student
    @$btn_rescore_problem_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text "Please enter a student email address or username."
      if not problem_to_reset
        return @$request_response_error_grade.text "Please enter a problem urlname."
      send_data =
        unique_student_identifier: unique_student_identifier
        problem_to_reset: problem_to_reset

      $.ajax
        dataType: 'json'
        url: @$btn_rescore_problem_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> alert "Started rescore problem task for problem '#{problem_to_reset}' and student '#{unique_student_identifier}'. Click the 'Show Background Task History for Student' button to see the status of the task."
        error: std_ajax_err => @$request_response_error_grade.text "Error starting a task to rescore problem '#{problem_to_reset}' for student '#{unique_student_identifier}'."

    # list task history for student+problem
    @$btn_task_history_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text "Please enter a student email address or username."
      if not problem_to_reset
        return @$request_response_error_grade.text "Please enter a problem urlname."
      send_data =
        unique_student_identifier: unique_student_identifier
        problem_urlname: problem_to_reset

      $.ajax
        dataType: 'json'
        url: @$btn_task_history_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then (data) =>
          create_task_list_table @$table_task_history_single, data.tasks
        error: std_ajax_err => @$request_response_error_grade.text "Error getting task history for student '#{unique_student_identifier}' and problem '#{problem_to_reset}'."

    # start task to reset attempts on problem for all students
    @$btn_reset_attempts_all.click =>
      problem_to_reset = @$field_problem_select_all.val()
      if not problem_to_reset
        return @$request_response_error_all.text "Please enter a problem urlname."
      if window.confirm "Reset attempts for all students on problem '#{@$field_problem_select_all.val()}'?"
        send_data =
          all_students: true
          problem_to_reset: problem_to_reset

        $.ajax
          dataType: 'json'
          url: @$btn_reset_attempts_all.data 'endpoint'
          data: send_data
          success: @clear_errors_then -> alert "Successfully started task to reset attempts for problem '#{problem_to_reset}'. Click the 'Show Background Task History for Problem' button to see the status of the task."
          error: std_ajax_err => @$request_response_error_all.text "Error starting a task to reset attempts for all students on this problem."
      else
        @clear_errors()

    # start task to rescore problem for all students
    @$btn_rescore_problem_all.click =>
      problem_to_reset = @$field_problem_select_all.val()
      if not problem_to_reset
        return @$request_response_error_all.text "Please enter a problem urlname."
      if window.confirm "Rescore problem '#{@$field_problem_select_all.val()}' for all students?"
        send_data =
          all_students: true
          problem_to_reset: problem_to_reset

        $.ajax
          dataType: 'json'
          url: @$btn_rescore_problem_all.data 'endpoint'
          data: send_data
          success: @clear_errors_then -> alert "Successfully started task to rescore problem '#{problem_to_reset}' for all students. Click the 'Show Background Task History for Problem' button to see the status of the task."
          error: std_ajax_err => @$request_response_error_all.text "Error starting a task to rescore this problem for all students."
      else
        @clear_errors()

    # list task history for problem
    @$btn_task_history_all.click =>
      send_data =
        problem_urlname: @$field_problem_select_all.val()

      if not send_data.problem_urlname
        return @$request_response_error_all.text "Please enter a problem urlname."

      $.ajax
        dataType: 'json'
        url: @$btn_task_history_all.data 'endpoint'
        data: send_data
        success: @clear_errors_then (data) =>
          create_task_list_table @$table_task_history_all, data.tasks
        error: std_ajax_err => @$request_response_error_all.text "Error listing task history for this student and problem."

  reload_running_tasks_list: =>
    list_endpoint = @$table_running_tasks.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: list_endpoint
      success: (data) => create_task_list_table @$table_running_tasks, data.tasks
      error: std_ajax_err => console.warn "error listing all instructor tasks"

  # wraps a function, but first clear the error displays
  clear_errors_then: (cb) ->
    @$request_response_error_progress.empty()
    @$request_response_error_grade.empty()
    @$request_response_error_all.empty()
    ->
      cb?.apply this, arguments


  clear_errors: ->
    @$request_response_error_progress.empty()
    @$request_response_error_grade.empty()
    @$request_response_error_all.empty()

  # handler for when the section title is clicked.
  onClickTitle: -> @task_poller?.start()

  # handler for when the section is closed
  onExit: -> @task_poller?.stop()


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    StudentAdmin: StudentAdmin
