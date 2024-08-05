package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"

	"html/template"
	"strings"

	"github.com/gin-gonic/gin"
)

func refreshData() {
	// do something
}

type LinealCupWinsByCountry struct {
	Country string
	Wins    int
}

type LinealCupStatistics struct {
	CurrentHolder string
	WinsByCountry []LinealCupWinsByCountry
}

func loadDataFromJSON(filename string) LinealCupStatistics {
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	var data LinealCupStatistics
	err = json.NewDecoder(file).Decode(&data)
	if err != nil {
		log.Fatal(err)
	}
	return data
}

func generateHTMLTable(data []LinealCupWinsByCountry) string {
	table := "<table class=\"w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400\">"
	table += "<thead class=\"text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400\">"
	table += "<tr><th scope=\"col\" class=\"px-6 py-3\">Team Name</th><th>Number of Wins</th></tr>"
	table += "</thead>"
	table += "<tbody>"

	for _, d := range data {
		table += "<tr class=\"bg-white border-b dark:bg-gray-800 dark:border-gray-700\">"
		table += "<td class=\"px-6\">" + d.Country + "</td>"
		table += "<td class=\"px-6\">" + strconv.Itoa(d.Wins) + "</td>"
		table += "</tr>"
	}
	table += "</tbody>"
	table += "</table>"
	return table
}

func main() {

	router := gin.Default()

	router.SetFuncMap(template.FuncMap{"upper": strings.ToUpper})

	router.Static("/assets", "./assets")
	router.LoadHTMLGlob("templates/*.html")

	haigShieldData := loadDataFromJSON("assets/men_lineal_cup_stats.json")
	haigTableHTML := generateHTMLTable(haigShieldData.WinsByCountry)

	signesShieldData := loadDataFromJSON("assets/women_lineal_cup_stats.json")
	signesTableHTML := generateHTMLTable(signesShieldData.WinsByCountry)

	router.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "index.html", gin.H{
			"haig_current_holder":   haigShieldData.CurrentHolder,
			"haig_table":            template.HTML(haigTableHTML),
			"signes_current_holder": signesShieldData.CurrentHolder,
			"signes_table":          template.HTML(signesTableHTML),
		})
	})

	router.GET("/about", func(c *gin.Context) {
		c.HTML(http.StatusOK, "about.html", gin.H{
			"title":   "Hello, About!",
			"content": "This is an about page...",
		})
	})

	router.Run(":8000")
}
